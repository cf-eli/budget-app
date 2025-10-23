from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SimpleFinAccountSchema(BaseModel):
    id: int
    account_id: str
    name: str
    currency: str
    balance: float
    available_balance: Optional[float]
    balance_date: datetime
    possible_error: bool
    extra: Optional[dict]
    updated_at: datetime

    model_config = {"from_attributes": True}