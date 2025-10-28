"""Transaction-related schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TransactionBudget(BaseModel):
    """Schema for budget information in transaction responses."""

    id: int
    name: str
    # Add other budget fields

    model_config = {"from_attributes": True}


class AccountOrg(BaseModel):
    """Schema for organization information in account responses."""

    id: int
    domain: str
    sfin_url: str
    url: str = ""
    name: str = ""

    model_config = {"from_attributes": True}


class TransactionAccount(BaseModel):
    """Schema for account information in transaction responses."""

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
    org: AccountOrg

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    """Response schema for transaction data with account and budget info."""

    id: int
    transaction_id: str
    amount: float
    description: str | None
    payee: str | None
    transacted_at: datetime
    pending: bool
    is_split: bool
    transaction_type: str | None
    exclude_from_budget: bool
    budget: TransactionBudget | None
    account: TransactionAccount

    model_config = {"from_attributes": True}


class TransactionTypeEnum(str, Enum):
    """Valid transaction types."""

    TRANSFER = "transfer"
    CREDIT_PAYMENT = "credit_payment"
    LOAN_PAYMENT = "loan_payment"


class TransactionLineItemResponse(BaseModel):
    """Response schema for transaction line item data."""

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
    """Response schema for transaction with breakdown line items."""

    id: int
    transaction_id: str
    amount: float
    description: str | None
    payee: str | None
    transacted_at: datetime
    is_split: bool
    transaction_type: str | None
    exclude_from_budget: bool
    budget_id: int | None
    line_items: list[TransactionLineItemResponse] = []

    model_config = {"from_attributes": True}


class MarkTransactionTypeRequest(BaseModel):
    """Request schema for marking transaction type and budget exclusion."""

    transaction_type: TransactionTypeEnum | None = None
    exclude_from_budget: bool = False


class CreateLineItemRequest(BaseModel):
    """Request schema for creating a new transaction line item."""

    description: str
    amount: float
    quantity: float | None = 1.0
    unit_price: float | None = None
    category: str | None = None
    budget_id: int | None = None
    notes: str | None = None


class CreateBreakdownRequest(BaseModel):
    """Request schema for creating transaction breakdown with multiple line items."""

    transaction_id: int
    line_items: list[CreateLineItemRequest]


class PaginatedTransactionResponse(BaseModel):
    """Response schema for paginated transaction list."""

    transactions: list[TransactionResponse]
    total: int
    page: int
    rows_per_page: int

    model_config = {"from_attributes": True}
