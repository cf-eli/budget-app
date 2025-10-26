"""Finance-related schemas for SimpleFIN API responses."""

from datetime import datetime

from pydantic import BaseModel


class SimpleFinTransactionSchema(BaseModel):
    """Schema for SimpleFIN transaction data."""

    id: int
    transaction_id: str
    posted: datetime | None
    amount: float
    description: str | None
    payee: str | None
    memo: str | None
    transacted_at: datetime
    pending: bool
    extra: dict | None
    updated_at: datetime
    budget_id: int | None
    account_id: str

    model_config = {"from_attributes": True}


class SimpleFinAccountSchema(BaseModel):
    """Schema for SimpleFIN account data."""

    id: int
    account_id: str
    name: str
    currency: str
    balance: float
    available_balance: float | None
    balance_date: datetime
    possible_error: bool
    extra: dict | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetSchema(BaseModel):
    """Schema for budget data."""

    id: int
    name: str
    # Add other budget fields

    model_config = {"from_attributes": True}


class UserSchema(BaseModel):
    """Schema for user data with accounts and budgets."""

    id: int
    auth_user_id: str
    access_url: str | None
    accounts: list[SimpleFinAccountSchema]
    budgets: list[BudgetSchema]

    model_config = {"from_attributes": True}


class GetTransactionResponse(BaseModel):
    """Response schema for retrieving a single transaction."""

    id: int
    transaction_id: str
    posted: datetime | None
    amount: float
    description: str | None
    payee: str | None
    memo: str | None
    transacted_at: datetime
    pending: bool
    extra: dict | None
    updated_at: datetime
    account: SimpleFinAccountSchema
    budget: BudgetSchema | None
    is_split: bool

    model_config = {"from_attributes": True}


class GetTransactionsListResponse(BaseModel):
    """Response schema for retrieving a list of transactions."""

    transactions: list[GetTransactionResponse]


class TransactionLineItemResponse(BaseModel):
    """Response schema for a transaction line item."""

    id: int
    description: str
    amount: float
    quantity: float | None
    unit_price: float | None
    category: str | None
    budget_id: int | None
    notes: str | None

    model_config = {"from_attributes": True}


class TransactionWithBreakdownResponse(BaseModel):
    """Response schema for a transaction with its breakdown line items."""

    id: int
    transaction_id: str
    amount: float
    description: str | None
    payee: str | None
    transacted_at: datetime
    is_split: bool
    budget_id: int | None
    line_items: list[TransactionLineItemResponse] = []

    model_config = {"from_attributes": True}


class CreateLineItemRequest(BaseModel):
    """Request schema for creating a transaction line item."""

    description: str
    amount: float
    quantity: float | None = 1.0
    unit_price: float | None = None
    category: str | None = None
    budget_id: int | None = None
    notes: str | None = None


class CreateBreakdownRequest(BaseModel):
    """Request schema for creating a transaction breakdown with line items."""

    transaction_id: int
    line_items: list[CreateLineItemRequest]
