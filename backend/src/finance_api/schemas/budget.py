from pydantic import BaseModel

class BudgetRequest(BaseModel):
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
    name: str
    id: int


class IncomeBudgetResponse(BaseModel):
    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float  # NEW: Total of transactions
    amount_after_transactions: float  # NEW: Expected + transactions

class ExpenseBudgetResponse(BaseModel):
    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float  # NEW
    amount_after_transactions: float  # NEW

class FundBudgetResponse(BaseModel):
    id: int
    user_id: int
    enable: bool
    deleted: bool
    priority: int | None
    increment: float | None
    current_amount: float | None
    max: float | None
    name: str
    transaction_sum: float  # NEW
    amount_after_transactions: float  # NEW

class FlexibleBudgetResponse(BaseModel):
    id: int
    user_id: int
    enable: bool
    deleted: bool
    fixed: bool
    expected_amount: float | None
    min: float | None
    max: float | None
    name: str
    transaction_sum: float  # NEW
    amount_after_transactions: float  # NEW

class AllBudgetsResponse(BaseModel):
    incomes: list[IncomeBudgetResponse] = []
    expenses: list[ExpenseBudgetResponse] = []
    flexibles: list[FlexibleBudgetResponse] = []
    funds: list[FundBudgetResponse] = []