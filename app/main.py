from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine, get_db
from app.models import TransactionRecord
from app.schemas import TransactionRequest, RiskAssessment, TransactionOut, HealthOut
from app.risk import assess_risk

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Demo convenience. In production, use Alembic migrations instead.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Transaction Risk Scoring API",
    version="1.0.0",
    description="Portfolio example demonstrating validation, risk scoring, persistence, idempotency and operational endpoints.",
    lifespan=lifespan,
)

@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        # Do not expose internal exception details to clients.
        response = JSONResponse(status_code=500, content={
            "detail": "Internal server error",
            "request_id": request_id,
        })
    response.headers["X-Request-ID"] = request_id
    return response

def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

@app.get("/health/live", response_model=HealthOut, tags=["operations"])
def liveness():
    return HealthOut(status="alive")

@app.get("/health/ready", response_model=HealthOut, tags=["operations"])
def readiness(db: Session = Depends(get_db)):
    # A database query verifies that the persistence layer is reachable.
    db.execute(select(func.count()).select_from(TransactionRecord)).scalar_one()
    return HealthOut(status="ready")

@app.post(
    "/v1/transactions/score",
    response_model=RiskAssessment,
    status_code=status.HTTP_200_OK,
    tags=["transactions"],
)
def score_transaction(
    payload: TransactionRequest,
    request: Request,
    response: Response,
    _auth: None = Depends(require_api_key),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        if len(idempotency_key) > 128 or not idempotency_key.strip():
            raise HTTPException(status_code=400, detail="Idempotency-Key must be 1-128 nonblank characters")
        existing = db.scalar(
            select(TransactionRecord).where(TransactionRecord.idempotency_key == idempotency_key)
        )
        if existing:
            response.headers["Idempotency-Replayed"] = "true"
            return RiskAssessment.model_validate(existing.to_result())

    result = assess_risk(payload)
    record = TransactionRecord(
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        amount=float(payload.amount),
        currency=payload.currency,
        country=payload.country,
        merchant_category=payload.merchant_category,
        risk_score=result.risk_score,
        decision=result.decision,
        reasons=result.reasons,
        request_id=request.state.request_id,
        idempotency_key=idempotency_key,
    )
    db.add(record)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # A concurrent duplicate idempotency key can race; return a safe conflict.
        raise HTTPException(status_code=409, detail="Could not persist transaction; check duplicate request")
    db.refresh(record)
    return result

@app.get("/v1/transactions/{transaction_id}", response_model=TransactionOut, tags=["transactions"])
def get_transaction(
    transaction_id: str,
    _auth: None = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    record = db.scalar(select(TransactionRecord).where(TransactionRecord.transaction_id == transaction_id))
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return record

@app.get("/v1/transactions", response_model=list[TransactionOut], tags=["transactions"])
def list_transactions(
    limit: int = 50,
    offset: int = 0,
    _auth: None = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be non-negative")
    return list(db.scalars(
        select(TransactionRecord).order_by(TransactionRecord.created_at.desc()).offset(offset).limit(limit)
    ).all())

@app.get("/metrics", tags=["operations"])
def metrics(_auth: None = Depends(require_api_key), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(TransactionRecord)) or 0
    blocked = db.scalar(
        select(func.count()).select_from(TransactionRecord).where(TransactionRecord.decision == "BLOCK")
    ) or 0
    review = db.scalar(
        select(func.count()).select_from(TransactionRecord).where(TransactionRecord.decision == "REVIEW")
    ) or 0
    return {
        "transactions_scored": total,
        "allow_count": total - blocked - review,
        "review_count": review,
        "block_count": blocked,
    }
