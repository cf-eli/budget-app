"""Transaction rule schemas for automated budget assignment."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RuleFieldEnum(str, Enum):
    """Fields that can be used in rule conditions."""

    PAYEE = "payee"
    DESCRIPTION = "description"
    AMOUNT = "amount"
    ACCOUNT_ID = "account_id"
    ACCOUNT_NAME = "account_name"
    ORG_DOMAIN = "org_domain"
    ORG_NAME = "org_name"


class RuleOperatorEnum(str, Enum):
    """Operators for rule conditions."""

    EXACT = "exact"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    RANGE = "range"


class RuleCondition(BaseModel):
    """A single condition in a rule."""

    field: RuleFieldEnum
    operator: RuleOperatorEnum
    value: str | float
    value2: float | None = None  # Only used for range operator


class CreateRuleRequest(BaseModel):
    """Request schema for creating a new rule."""

    name: str
    target_budget_id: int
    conditions: list[RuleCondition] = Field(min_length=1)
    priority: int = 0
    is_active: bool = True


class UpdateRuleRequest(BaseModel):
    """Request schema for updating a rule."""

    name: str | None = None
    target_budget_id: int | None = None
    conditions: list[RuleCondition] | None = None
    priority: int | None = None
    is_active: bool | None = None


class RuleResponse(BaseModel):
    """Response schema for a rule."""

    id: int
    name: str
    target_budget_id: int
    target_budget_name: str | None
    conditions: list[RuleCondition]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderRulesRequest(BaseModel):
    """Request schema for reordering rules."""

    rule_ids: list[int] = Field(min_length=1)


class RulePreviewItem(BaseModel):
    """A single transaction in the rule application preview."""

    transaction_id: int
    transaction_description: str
    transaction_payee: str | None
    transaction_amount: float
    transacted_at: datetime
    account_name: str
    org_name: str | None
    rule_name: str
    rule_id: int
    target_budget_id: int
    target_budget_name: str | None
    current_budget_id: int | None
    current_budget_name: str | None
    selected: bool = True  # For UI checkbox state


class RulePreviewRequest(BaseModel):
    """Request schema for previewing rule application."""

    month: int
    year: int
    override_existing: bool = False


class RulePreviewResponse(BaseModel):
    """Response schema for rule application preview."""

    assignments: list[RulePreviewItem]
    total_count: int
    already_assigned_count: int
    new_assignment_count: int


class ApplyRulesRequest(BaseModel):
    """Request schema for applying rules to transactions."""

    transaction_ids: list[int] = Field(min_length=1)
    override_existing: bool = False


class ApplyRulesResponse(BaseModel):
    """Response schema for rule application."""

    applied_count: int
    skipped_count: int
    error_count: int
