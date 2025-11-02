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
    month_amount: float | None = None  # For funds: amount added this month
    master_fund_id: int | None = None  # Optional: link to existing master
    month: int
    year: int


class BudgetNameResponse(BaseModel):
    """Response schema for budget name and ID."""

    name: str
    id: int
    master_id: int | None = None  # Only populated for funds, None for regular budgets


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
    master_balance: float  # Balance from master fund
    month_amount: float  # Amount added/allocated this specific month
    max: float | None
    name: str
    transaction_sum: float
    amount_after_transactions: float
    carryover: float
    master_fund_id: int  # ID of the master fund
    master_fund_name: str | None  # Name of the master fund family


class FundCombineRequest(BaseModel):
    """Request schema for combining a fund with another fund's master."""

    target_fund_id: int  # ID of fund whose master to combine with


class FundUnlinkRequest(BaseModel):
    """Request schema for unlinking a fund and splitting its master."""

    keep_amount: float  # Amount to keep with this fund's new master


class FundCalculationBreakdown(BaseModel):
    """Schema for fund calculation breakdown."""

    fund_id: int
    fund_name: str
    month: int
    year: int
    master_id: int
    master_name: str | None
    master_balance: float
    transactions: float


class FundCalculationResponse(BaseModel):
    """Response schema for fund calculation."""

    fund_id: int
    name: str
    priority: int
    increment: float
    max: float | None
    master_balance: float  # Balance from master fund
    month_amount: float  # Amount added this month
    calculated_amount: float  # Total balance (master + transactions)
    transactions: float  # Sum of transactions
    breakdown: list[FundCalculationBreakdown]
    master_id: int  # ID of the master fund


class ApplyFundIncrementsRequest(BaseModel):
    """Request schema for applying fund increments."""

    month: int
    year: int
    safe_mode: bool = False


class FundApplicationDetail(BaseModel):
    """Detail of a fund application."""

    fund_id: int
    fund_name: str
    amount_added: float | None = None
    new_amount: float | None = None
    reason: str | None = None


class ApplyFundIncrementsResponse(BaseModel):
    """Response schema for applying fund increments."""

    applied_funds: list[FundApplicationDetail]
    skipped_funds: list[FundApplicationDetail]
    balance_before: float
    balance_after: float
    total_applied: float
    would_go_negative: bool


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


class FundInMaster(BaseModel):
    """Individual fund within a master fund."""

    fund_id: int
    budget_name: str
    month: int
    year: int
    month_amount: float  # Amount contributed this month
    transactions: float  # Amount withdrawn (negative value)
    net_contribution: float  # month_amount + transactions


class MasterFundDetailsResponse(BaseModel):
    """Details of a master fund and all its associated funds."""

    master_id: int
    master_name: str | None
    total_balance: float  # Current master fund balance
    funds: list[FundInMaster]  # Ordered by year, month (oldest to newest)


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


class OrphanedMasterInfo(BaseModel):
    """Info about an orphaned fund master."""

    master_id: int
    name: str
    balance: float
    last_active_month: int | None
    last_active_year: int | None
    last_fund_name: str | None


class OrphanedMastersRequest(BaseModel):
    """Request schema for getting orphaned masters."""

    month: int
    year: int


class OrphanedMastersResponse(BaseModel):
    """Response schema for orphaned masters."""

    orphaned_masters: list[OrphanedMasterInfo]


class DiscontinueMasterRequest(BaseModel):
    """Request schema for discontinuing a fund master."""

    month: int
    year: int


class AddMonthToMasterRequest(BaseModel):
    """Request schema for adding a fund to an orphaned master."""

    month: int
    year: int
    priority: int
    increment: float
    max: float | None = None
