"""Transaction rule API endpoints."""

from litestar import Router, delete, get, patch, post, put, status_codes
from litestar.exceptions import NotFoundException

from finance_api.crud.rule import (
    apply_rules_to_transactions,
    create_rule,
    delete_rule,
    get_rule,
    get_rules,
    preview_rule_application,
    reorder_rules,
    update_rule,
)
from finance_api.models.transaction_rule import TransactionRule
from finance_api.models.user import User
from finance_api.schemas.rules import (
    ApplyRulesRequest,
    ApplyRulesResponse,
    CreateRuleRequest,
    ReorderRulesRequest,
    RuleCondition,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
    UpdateRuleRequest,
)
from finance_api.schemas.schema import MessageResponse


def _rule_to_response(rule: TransactionRule) -> RuleResponse:
    """Convert a TransactionRule model to RuleResponse schema."""
    conditions = [RuleCondition(**cond) for cond in rule.conditions]
    return RuleResponse(
        id=rule.id,
        name=rule.name,
        target_budget_id=rule.target_budget_id,
        target_budget_name=rule.target_budget.name if rule.target_budget else None,
        conditions=conditions,
        priority=rule.priority,
        is_active=rule.is_active,
        target_transaction_type=rule.target_transaction_type,
        target_exclude_from_budget=rule.target_exclude_from_budget,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@get("/", response=list[RuleResponse])
async def get_rules_endpoint(
    user: User,
    include_inactive: bool = False,
) -> list[RuleResponse]:
    """
    Get all transaction rules for the user.

    Returns rules ordered by priority (lowest first = highest priority).
    """
    rules = await get_rules(user.id, include_inactive=include_inactive)
    return [_rule_to_response(rule) for rule in rules]


@post("/", response=RuleResponse, status_code=status_codes.HTTP_201_CREATED)
async def create_rule_endpoint(
    user: User,
    data: CreateRuleRequest,
) -> RuleResponse:
    """Create a new transaction rule."""
    rule = await create_rule(user.id, data)
    return _rule_to_response(rule)


@get("/{rule_id:int}", response=RuleResponse)
async def get_rule_endpoint(
    user: User,
    rule_id: int,
) -> RuleResponse:
    """Get a specific rule by ID."""
    rule = await get_rule(rule_id, user.id)
    if not rule:
        msg = f"Rule {rule_id} not found"
        raise NotFoundException(msg)
    return _rule_to_response(rule)


@put("/{rule_id:int}", response=RuleResponse)
async def update_rule_endpoint(
    user: User,
    rule_id: int,
    data: UpdateRuleRequest,
) -> RuleResponse:
    """Update a rule."""
    rule = await update_rule(rule_id, user.id, data)
    if not rule:
        msg = f"Rule {rule_id} not found"
        raise NotFoundException(msg)
    return _rule_to_response(rule)


@delete("/{rule_id:int}", status_code=status_codes.HTTP_204_NO_CONTENT)
async def delete_rule_endpoint(
    user: User,
    rule_id: int,
) -> None:
    """Delete a rule."""
    deleted = await delete_rule(rule_id, user.id)
    if not deleted:
        msg = f"Rule {rule_id} not found"
        raise NotFoundException(msg)


@patch("/reorder", response=MessageResponse)
async def reorder_rules_endpoint(
    user: User,
    data: ReorderRulesRequest,
) -> MessageResponse:
    """
    Reorder rules by setting priorities.

    Pass a list of rule IDs in the desired order.
    The first ID will have highest priority (priority=0).
    """
    await reorder_rules(user.id, data.rule_ids)
    return MessageResponse(message="Rules reordered successfully")


@post("/preview", response=RulePreviewResponse, status_code=status_codes.HTTP_200_OK)
async def preview_rules_endpoint(
    user: User,
    data: RulePreviewRequest,
) -> RulePreviewResponse:
    """
    Preview which transactions would be assigned by rules.

    This is a dry-run that shows what would happen without making changes.
    """
    return await preview_rule_application(
        user.id,
        data.month,
        data.year,
        override_existing=data.override_existing,
    )


@post("/apply", response=ApplyRulesResponse, status_code=status_codes.HTTP_200_OK)
async def apply_rules_endpoint(
    user: User,
    data: ApplyRulesRequest,
) -> ApplyRulesResponse:
    """
    Apply rules to selected transactions.

    Pass the transaction IDs selected from the preview.
    """
    return await apply_rules_to_transactions(
        user.id,
        data.transaction_ids,
        override_existing=data.override_existing,
    )


# Router setup
rules_router = Router(
    path="/api/v1/rules",
    route_handlers=[
        get_rules_endpoint,
        create_rule_endpoint,
        get_rule_endpoint,
        update_rule_endpoint,
        delete_rule_endpoint,
        reorder_rules_endpoint,
        preview_rules_endpoint,
        apply_rules_endpoint,
    ],
    tags=["Rules"],
)
