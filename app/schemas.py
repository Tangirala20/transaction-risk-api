from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class TransactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transaction_id: str = Field(min_length=1, max_length=80)
    user_id: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    country: str = Field(pattern=r"^[A-Z]{2}$")
    merchant_category: str = Field(min_length=1, max_length=50)

    @field_validator("transaction_id", "user_id", "merchant_category")
    @classmethod
    def nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank")
        return value

class RiskAssessment(BaseModel):
    transaction_id: str
    risk_score: float = Field(ge=0, le=1)
    decision: Literal["ALLOW", "REVIEW", "BLOCK"]
    reasons: list[str]

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    country: str
    merchant_category: str
    risk_score: float
    decision: str
    request_id: str
    idempotency_key: str | None
    created_at: datetime

class HealthOut(BaseModel):
    status: str
