"""Rule application logic for matching and assigning transactions."""

from calendar import monthrange
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.crud.rule.base import get_rules
from finance_api.models.account import SimpleFinAccount
from finance_api.models.budget import Budget
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction
from finance_api.schemas.rules import (
    ApplyRulesResponse,
    RuleCondition,
    RuleFieldEnum,
    RuleOperatorEnum,
    RulePreviewItem,
    RulePreviewResponse,
)

if TYPE_CHECKING:
    from finance_api.models.transaction_rule import TransactionRule


def _get_field_value(
    transaction: SimpleFinTransaction,
    field: RuleFieldEnum,
) -> str | float:
    """Extract the field value from a transaction based on field type."""
    field_map = {
        RuleFieldEnum.PAYEE: transaction.payee or "",
        RuleFieldEnum.DESCRIPTION: transaction.description or "",
        RuleFieldEnum.AMOUNT: transaction.amount,
        RuleFieldEnum.ACCOUNT_ID: transaction.account_id,
        RuleFieldEnum.ACCOUNT_NAME: (
            transaction.account.name if transaction.account else ""
        ),
        RuleFieldEnum.ORG_DOMAIN: (
            transaction.account.org.domain
            if transaction.account and transaction.account.org
            else ""
        ),
        RuleFieldEnum.ORG_NAME: (
            transaction.account.org.name
            if transaction.account and transaction.account.org
            else ""
        ),
    }
    return field_map.get(field, "")


def _apply_text_operator(
    field_value: str | float,
    condition: RuleCondition,
) -> bool:
    """Apply text-based operators (exact, contains)."""
    if condition.operator == RuleOperatorEnum.EXACT:
        return str(field_value).lower() == str(condition.value).lower()
    if condition.operator == RuleOperatorEnum.CONTAINS:
        return str(condition.value).lower() in str(field_value).lower()
    return False


def _apply_numeric_operator(
    field_value: str | float,
    condition: RuleCondition,
) -> bool:
    """Apply numeric operators (greater_than, less_than, range)."""
    try:
        numeric_value = float(field_value)  # type: ignore[arg-type]
        if condition.operator == RuleOperatorEnum.GREATER_THAN:
            return numeric_value > float(condition.value)
        if condition.operator == RuleOperatorEnum.LESS_THAN:
            return numeric_value < float(condition.value)
        if condition.operator == RuleOperatorEnum.RANGE:
            return (
                float(condition.value)
                <= numeric_value
                <= float(
                    condition.value2 or 0,
                )
            )
    except (TypeError, ValueError):
        return False
    return False


def _matches_condition(
    transaction: SimpleFinTransaction,
    condition: RuleCondition,
) -> bool:
    """Check if a transaction matches a single condition."""
    field_value = _get_field_value(transaction, condition.field)

    # Text operators
    if condition.operator in (RuleOperatorEnum.EXACT, RuleOperatorEnum.CONTAINS):
        return _apply_text_operator(field_value, condition)

    # Numeric operators
    return _apply_numeric_operator(field_value, condition)


def _matches_all_conditions(
    transaction: SimpleFinTransaction,
    conditions: list[dict],
) -> bool:
    """Check if a transaction matches ALL conditions (AND logic)."""
    for cond_dict in conditions:
        condition = RuleCondition(**cond_dict)
        if not _matches_condition(transaction, condition):
            return False
    return True


async def _get_transactions_for_rules(
    user_id: int,
    month: int,
    year: int,
    include_pending: bool = False,
    session: AsyncSession | None = None,
) -> list[SimpleFinTransaction]:
    """Get transactions for a month that are eligible for rule application."""
    async with get_session(session) as sess:
        # Calculate month date range
        month_start = datetime(year, month, 1, tzinfo=UTC)
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
            .where(SimpleFinTransaction.transacted_at >= month_start)
            .where(SimpleFinTransaction.transacted_at <= month_end)
            .where(~SimpleFinTransaction.exclude_from_budget)
            .options(selectinload(SimpleFinTransaction.budget))
            .options(
                selectinload(SimpleFinTransaction.account).selectinload(
                    SimpleFinAccount.org,
                ),
            )
        )

        if not include_pending:
            stmt = stmt.where(~SimpleFinTransaction.pending)

        result = await sess.execute(stmt)
        return list(result.scalars().all())


async def _get_budget_for_month(
    user_id: int,
    budget_name: str,
    month: int,
    year: int,
    session: AsyncSession,
) -> Budget | None:
    """
    Find a budget by name for a specific month/year.

    Rules store a target_budget_id, but budgets are month-specific.
    This function finds the equivalent budget for the target month/year.
    """
    stmt = (
        select(Budget)
        .where(Budget.user_id == user_id)
        .where(Budget.name == budget_name)
        .where(Budget.month == month)
        .where(Budget.year == year)
        .where(~Budget.deleted)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _resolve_budgets_for_rules(
    user_id: int,
    rules: list["TransactionRule"],
    month: int,
    year: int,
    session: AsyncSession,
) -> dict[str, Budget]:
    """Pre-resolve budgets for rules to the target month/year."""
    resolved_budgets: dict[str, Budget] = {}
    for rule in rules:
        if rule.target_budget and rule.target_budget.name:
            budget_name = rule.target_budget.name
            if budget_name not in resolved_budgets:
                budget = await _get_budget_for_month(
                    user_id,
                    budget_name,
                    month,
                    year,
                    session,
                )
                if budget:
                    resolved_budgets[budget_name] = budget
    return resolved_budgets


def _build_preview_item(
    transaction: SimpleFinTransaction,
    rule: "TransactionRule",
    resolved_budget: Budget | None = None,
) -> RulePreviewItem:
    """Build a RulePreviewItem from a transaction and matching rule."""
    # Use resolved budget for the target month, fall back to rule's target
    if resolved_budget:
        target_id = resolved_budget.id
        target_name = resolved_budget.name
    else:
        target_id = rule.target_budget_id
        target_name = rule.target_budget.name if rule.target_budget else None

    return RulePreviewItem(
        transaction_id=transaction.id,
        transaction_description=transaction.description or "",
        transaction_payee=transaction.payee,
        transaction_amount=transaction.amount,
        transacted_at=transaction.transacted_at,
        account_name=transaction.account.name if transaction.account else "",
        org_name=(
            transaction.account.org.name
            if transaction.account and transaction.account.org
            else None
        ),
        rule_name=rule.name,
        rule_id=rule.id,
        target_budget_id=target_id,
        target_budget_name=target_name,
        current_budget_id=transaction.budget_id,
        current_budget_name=transaction.budget.name if transaction.budget else None,
        selected=True,
    )


def _get_resolved_budget_for_rule(
    rule: "TransactionRule",
    resolved_budgets: dict[str, Budget],
) -> Budget | None:
    """Get the resolved budget for a rule from the pre-resolved cache."""
    budget_name = rule.target_budget.name if rule.target_budget else None
    return resolved_budgets.get(budget_name) if budget_name else None


async def preview_rule_application(
    user_id: int,
    month: int,
    year: int,
    override_existing: bool = False,
    session: AsyncSession | None = None,
) -> RulePreviewResponse:
    """
    Preview which transactions would be assigned to budgets.

    Returns a list of matches without making any changes.
    Rules are resolved to the correct budget for the target month/year.
    """
    async with get_session(session) as sess:
        rules = await get_rules(user_id, include_inactive=False, session=sess)
        if not rules:
            return RulePreviewResponse(
                assignments=[],
                total_count=0,
                already_assigned_count=0,
                new_assignment_count=0,
            )

        resolved_budgets = await _resolve_budgets_for_rules(
            user_id,
            rules,
            month,
            year,
            sess,
        )

        transactions = await _get_transactions_for_rules(
            user_id,
            month,
            year,
            include_pending=False,
            session=sess,
        )

        assignments: list[RulePreviewItem] = []
        already_assigned_count = 0
        new_assignment_count = 0
        matched_transaction_ids: set[int] = set()

        for rule in rules:
            resolved_budget = _get_resolved_budget_for_rule(rule, resolved_budgets)
            if not resolved_budget:
                continue

            for transaction in transactions:
                if not _should_process_transaction(
                    transaction,
                    matched_transaction_ids,
                    override_existing,
                ):
                    continue
                if not _matches_all_conditions(transaction, rule.conditions):
                    continue

                matched_transaction_ids.add(transaction.id)

                if transaction.budget_id is not None:
                    already_assigned_count += 1
                else:
                    new_assignment_count += 1

                assignments.append(
                    _build_preview_item(transaction, rule, resolved_budget),
                )

        return RulePreviewResponse(
            assignments=assignments,
            total_count=len(assignments),
            already_assigned_count=already_assigned_count,
            new_assignment_count=new_assignment_count,
        )


def _should_process_transaction(
    transaction: SimpleFinTransaction,
    matched_ids: set[int],
    override_existing: bool,
) -> bool:
    """Check if a transaction should be processed for rule matching."""
    if transaction.id in matched_ids:
        return False
    return not (transaction.budget_id and not override_existing)


async def auto_apply_rules_for_user(
    user_id: int,
    session: AsyncSession | None = None,
) -> ApplyRulesResponse:
    """
    Automatically apply rules to all unassigned transactions in the current month.

    Used after syncing new transactions when user has auto_apply_rules enabled.
    Only assigns to transactions without an existing budget assignment.
    Rules are resolved to the correct budget for the current month/year.
    """
    now = datetime.now(UTC)
    month = now.month
    year = now.year

    async with get_session(session) as sess:
        rules = await get_rules(user_id, include_inactive=False, session=sess)
        if not rules:
            return ApplyRulesResponse(applied_count=0, skipped_count=0, error_count=0)

        resolved_budgets = await _resolve_budgets_for_rules(
            user_id,
            rules,
            month,
            year,
            sess,
        )

        transactions = await _get_transactions_for_rules(
            user_id,
            month,
            year,
            include_pending=False,
            session=sess,
        )

        unassigned = [t for t in transactions if t.budget_id is None]
        if not unassigned:
            return ApplyRulesResponse(applied_count=0, skipped_count=0, error_count=0)

        applied_count = 0
        error_count = 0

        for transaction in unassigned:
            matched_rule = next(
                (
                    r
                    for r in rules
                    if _matches_all_conditions(transaction, r.conditions)
                ),
                None,
            )

            if not matched_rule:
                continue

            resolved_budget = _get_resolved_budget_for_rule(
                matched_rule,
                resolved_budgets,
            )
            if not resolved_budget:
                continue

            try:
                await sess.execute(
                    update(SimpleFinTransaction)
                    .where(SimpleFinTransaction.id == transaction.id)
                    .values(budget_id=resolved_budget.id),
                )
                applied_count += 1
            except SQLAlchemyError:
                error_count += 1

        await sess.commit()

        return ApplyRulesResponse(
            applied_count=applied_count,
            skipped_count=len(unassigned) - applied_count - error_count,
            error_count=error_count,
        )


async def apply_rules_to_transactions(
    user_id: int,
    transaction_ids: list[int],
    override_existing: bool = False,
    session: AsyncSession | None = None,
) -> ApplyRulesResponse:
    """
    Apply rules to specific transactions selected by the user.

    This expects transaction_ids to be pre-filtered from the preview response.
    Rules are resolved to the correct budget for each transaction's month/year.
    """
    async with get_session(session) as sess:
        rules = await get_rules(user_id, include_inactive=False, session=sess)
        if not rules:
            return ApplyRulesResponse(
                applied_count=0,
                skipped_count=len(transaction_ids),
                error_count=0,
            )

        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(
                SimpleFinAccount.user_id == user_id,
                SimpleFinTransaction.id.in_(transaction_ids),
            )
            .options(
                selectinload(SimpleFinTransaction.account).selectinload(
                    SimpleFinAccount.org,
                ),
            )
        )
        result = await sess.execute(stmt)
        transactions = list(result.scalars().all())

        # Cache resolved budgets by (budget_name, month, year)
        resolved_budgets: dict[tuple[str, int, int], Budget | None] = {}

        applied_count = 0
        skipped_count = 0
        error_count = 0

        for transaction in transactions:
            if transaction.budget_id and not override_existing:
                skipped_count += 1
                continue

            matched_rule = next(
                (
                    r
                    for r in rules
                    if _matches_all_conditions(transaction, r.conditions)
                ),
                None,
            )

            if not matched_rule:
                skipped_count += 1
                continue

            # Resolve to month-appropriate budget based on transaction date
            budget_name = (
                matched_rule.target_budget.name if matched_rule.target_budget else None
            )
            if not budget_name:
                skipped_count += 1
                continue

            # Get month/year from transaction date
            txn_month = transaction.transacted_at.month
            txn_year = transaction.transacted_at.year
            cache_key = (budget_name, txn_month, txn_year)

            # Check cache first
            if cache_key not in resolved_budgets:
                resolved_budgets[cache_key] = await _get_budget_for_month(
                    user_id,
                    budget_name,
                    txn_month,
                    txn_year,
                    sess,
                )

            resolved_budget = resolved_budgets[cache_key]

            # Skip if no budget exists for this month
            if not resolved_budget:
                skipped_count += 1
                continue

            try:
                await sess.execute(
                    update(SimpleFinTransaction)
                    .where(SimpleFinTransaction.id == transaction.id)
                    .values(budget_id=resolved_budget.id),
                )
                applied_count += 1
            except SQLAlchemyError:
                error_count += 1

        await sess.commit()

        return ApplyRulesResponse(
            applied_count=applied_count,
            skipped_count=skipped_count,
            error_count=error_count,
        )
