from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class TransactionCreate(BaseModel):
    source_account_id: str
    destination_account_id: str
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    channel: str
    occurred_at: datetime
    transaction_type: str = "NORMAL"


class TransactionResponse(BaseModel):
    transaction_id: str
    event_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str
    channel: str
    occurred_at: datetime
    transaction_type: str
class AlertStatusUpdate(BaseModel):
    status: str
# ============================================================
# CASE MANAGEMENT MODELS
# ============================================================

class CaseCreate(BaseModel):
    alert_id: str
    priority: str = "MEDIUM"
    assigned_to: str | None = None
    notes: str | None = None


class CaseUpdate(BaseModel):
    case_status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    disposition: str | None = None
    notes: str | None = None