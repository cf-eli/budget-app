"""Budget request and response schemas."""

from pydantic import BaseModel


class BudgetRequest(BaseModel):
    """Request schema for creating or updating a budget."""

    name: str
    fixed: bool = True
    flexible: bool = False
    budget_type: str
    expected_amount: float | None = None
    min: float | None = None
    max: float | None = None
    priority: int | None = None
    increment: float | None = None
    current_amount: float | None = None
    month: int
    year: int


class BudgetNameResponse(BaseModel):
    """Response schema for budget name and ID."""

    name: str
    id: int


class IncomeBudgetResponse(BaseModel):
    """Response schema for income budget."""

    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float
    amount_after_transactions: float
    carryover: float


class ExpenseBudgetResponse(BaseModel):
    """Response schema for expense budget."""

    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float
    amount_after_transactions: float
    carryover: float


class FundBudgetResponse(BaseModel):
    """Response schema for fund budget."""

    id: int
    user_id: int
    enable: bool
    deleted: bool
    priority: int | None
    increment: float | None
    current_amount: float | None
    max: float | None
    name: str
    transaction_sum: float
    amount_after_transactions: float
    carryover: float


class FlexibleBudgetResponse(BaseModel):
    """Response schema for flexible budget."""

    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float
    amount_after_transactions: float
    carryover: float


class AllBudgetsResponse(BaseModel):
    """Response schema for all budget categories."""

    incomes: list[IncomeBudgetResponse] = []
    expenses: list[ExpenseBudgetResponse] = []
    flexibles: list[FlexibleBudgetResponse] = []
    funds: list[FundBudgetResponse] = []


class CopyBudgetsRequest(BaseModel):
    """Request schema for copying budgets from previous month."""

    target_month: int
    target_year: int
    source_month: int | None = None
    source_year: int | None = None


class CopiedBudgetCounts(BaseModel):
    """Schema for counts of copied budgets by type."""

    income: int
    expense: int
    flexible: int
    fund: int


class CopyBudgetsResponse(BaseModel):
    """Response schema for copy budgets operation."""

    message: str
    copied_budgets: CopiedBudgetCounts
    source_month: int
    source_year: int
