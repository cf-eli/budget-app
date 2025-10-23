from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime



class TransactionBudget(BaseModel):
    id: int
    name: str
    # Add other budget fields
    
    model_config = {"from_attributes": True}
class AccountOrg(BaseModel):
    id: int
    domain: str
    sfin_url: str
    url: str = ""
    name: str = ""

    model_config = {"from_attributes": True}

class TransactionAccount(BaseModel):
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
    org: AccountOrg

    model_config = {"from_attributes": True}

class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    amount: float
    description: Optional[str]
    payee: Optional[str]
    transacted_at: datetime
    pending: bool
    is_split: bool
    transaction_type: Optional[str]
    exclude_from_budget: bool
    budget: Optional[TransactionBudget]
    account: TransactionAccount

    model_config = {"from_attributes": True}

class TransactionTypeEnum(str, Enum):
    """Valid transaction types"""
    TRANSFER = "transfer"
    CREDIT_PAYMENT = "credit_payment"
    LOAN_PAYMENT = "loan_payment"

class TransactionLineItemResponse(BaseModel):
    id: int
    description: str
    amount: float
    quantity: Optional[float]
    unit_price: Optional[float]
    category: Optional[str]
    budget_id: Optional[int]
    notes: Optional[str]
    
    model_config = {"from_attributes": True}

class TransactionWithBreakdownResponse(BaseModel):
    id: int
    transaction_id: str
    amount: float
    description: Optional[str]
    payee: Optional[str]
    transacted_at: datetime
    is_split: bool
    transaction_type: Optional[str]
    exclude_from_budget: bool
    budget_id: Optional[int]
    line_items: list[TransactionLineItemResponse] = []
    
    model_config = {"from_attributes": True}

class MarkTransactionTypeRequest(BaseModel):
    transaction_type: Optional[TransactionTypeEnum] = None
    exclude_from_budget: bool = False

class CreateLineItemRequest(BaseModel):
    description: str
    amount: float
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = None
    category: Optional[str] = None
    budget_id: Optional[int] = None
    notes: Optional[str] = None

class CreateBreakdownRequest(BaseModel):
    transaction_id: int
    line_items: list[CreateLineItemRequest]