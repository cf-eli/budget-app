from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SimpleFinTransactionSchema(BaseModel):
    id: int
    transaction_id: str
    posted: Optional[datetime]
    amount: float
    description: Optional[str]
    payee: Optional[str]
    memo: Optional[str]
    transacted_at: datetime
    pending: bool
    extra: Optional[dict]
    updated_at: datetime
    budget_id: Optional[int]
    account_id: str

    
    model_config = {"from_attributes": True}

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
    # transactions: List[SimpleFinTransactionSchema]
    
    model_config = {"from_attributes": True}

class BudgetSchema(BaseModel):
    id: int
    name: str
    # Add other budget fields
    
    model_config = {"from_attributes": True}

class UserSchema(BaseModel):
    id: int
    auth_user_id: str
    access_url: Optional[str]
    accounts: List[SimpleFinAccountSchema]
    budgets: List[BudgetSchema]
    
    model_config = {"from_attributes": True}



class GetTransactionResponse(BaseModel):
    id: int
    transaction_id: str
    posted: Optional[datetime]
    amount: float
    description: Optional[str]
    payee: Optional[str]
    memo: Optional[str]
    transacted_at: datetime
    pending: bool
    extra: Optional[dict]
    updated_at: datetime
    account: SimpleFinAccountSchema
    budget: Optional[BudgetSchema]
    is_split: bool

    
    model_config = {"from_attributes": True}

class GetTransactionsListResponse(BaseModel):
    transactions: List[GetTransactionResponse]



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
    budget_id: Optional[int]
    line_items: list[TransactionLineItemResponse] = []
    
    model_config = {"from_attributes": True}

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