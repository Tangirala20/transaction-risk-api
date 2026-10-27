import json
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class TransactionRecord(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_transaction_id"),
        UniqueConstraint("idempotency_key", name="uq_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(80), nullable=False)
    user_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    merchant_category: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def reasons(self):
        return json.loads(self.reasons_json)

    def to_result(self):
        return {
            "transaction_id": self.transaction_id,
            "risk_score": self.risk_score,
            "decision": self.decision,
            "reasons": self.reasons,
        }
