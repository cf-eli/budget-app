"""Rule application logic for matching and assigning transactions."""

from calendar import monthrange
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.crud.rule.base import get_rules
from finance_api.crud.rule.matching import matches_all_conditions
from finance_api.models.account import SimpleFinAccount
from finance_api.models.budget import Budget
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction
from finance_api.schemas.rules import ApplyRulesResponse

if TYPE_CHECKING:
    from finance_api.models.transaction_rule import TransactionRule


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


def _get_resolved_budget_for_rule(
    rule: "TransactionRule",
    resolved_budgets: dict[str, Budget],
) -> Budget | None:
    """Get the resolved budget for a rule from the pre-resolved cache."""
    budget_name = rule.target_budget.name if rule.target_budget else None
    return resolved_budgets.get(budget_name) if budget_name else None


def _build_update_values(
    rule: "TransactionRule",
    resolved_budgets: dict[str, Budget],
) -> dict:
    """Build the update values dict for applying a rule to a transaction."""
    values: dict = {}
    resolved_budget = _get_resolved_budget_for_rule(rule, resolved_budgets)
    if rule.target_budget_id is not None and resolved_budget:
        values["budget_id"] = resolved_budget.id
    if rule.target_transaction_type is not None:
        values["transaction_type"] = rule.target_transaction_type
        values["exclude_from_budget"] = rule.target_exclude_from_budget
    return values


def _should_process_transaction(
    transaction: SimpleFinTransaction,
    rule: "TransactionRule",
    matched_ids: set[int],
    override_existing: bool,
) -> bool:
    """Check if a transaction should be processed for rule matching."""
    if transaction.id in matched_ids:
        return False
    # Type-only rules can apply to transactions that already have budgets
    if rule.target_transaction_type and not rule.target_budget_id:
        return transaction.transaction_type is None or override_existing
    return not (transaction.budget_id and not override_existing)


def _should_auto_apply(
    transaction: SimpleFinTransaction,
    rule: "TransactionRule",
) -> bool:
    """Check if a rule should auto-apply to a transaction."""
    # Budget rules: only apply to unassigned transactions
    if rule.target_budget_id and transaction.budget_id is not None:
        return False
    # Type rules: only apply if transaction has no type yet
    if rule.target_transaction_type and transaction.transaction_type is not None:
        return False
    # Must have at least one applicable action
    needs_budget = rule.target_budget_id and not transaction.budget_id
    needs_type = (
        rule.target_transaction_type
        and not transaction.transaction_type
    )
    return bool(needs_budget or needs_type)


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

        if not transactions:
            return ApplyRulesResponse(applied_count=0, skipped_count=0, error_count=0)

        applied_count = 0
        error_count = 0

        for transaction in transactions:
            matched_rule = next(
                (
                    r
                    for r in rules
                    if _should_auto_apply(transaction, r)
                    and matches_all_conditions(transaction, r.conditions)
                ),
                None,
            )

            if not matched_rule:
                continue

            update_values = _build_update_values(
                matched_rule,
                resolved_budgets,
            )
            if not update_values:
                continue

            try:
                await sess.execute(
                    update(SimpleFinTransaction)
                    .where(SimpleFinTransaction.id == transaction.id)
                    .values(**update_values),
                )
                applied_count += 1
            except SQLAlchemyError:
                error_count += 1

        await sess.commit()

        return ApplyRulesResponse(
            applied_count=applied_count,
            skipped_count=len(transactions) - applied_count - error_count,
            error_count=error_count,
        )


async def _resolve_update_values(
    user_id: int,
    transaction: SimpleFinTransaction,
    rule: "TransactionRule",
    budget_cache: dict[tuple[str, int, int], Budget | None],
    session: AsyncSession,
) -> dict:
    """Build update values for applying a rule to a specific transaction."""
    values: dict = {}

    # Handle budget assignment
    budget_name = rule.target_budget.name if rule.target_budget else None
    if budget_name:
        txn_month = transaction.transacted_at.month
        txn_year = transaction.transacted_at.year
        cache_key = (budget_name, txn_month, txn_year)

        if cache_key not in budget_cache:
            budget_cache[cache_key] = await _get_budget_for_month(
                user_id,
                budget_name,
                txn_month,
                txn_year,
                session,
            )

        resolved_budget = budget_cache[cache_key]
        if resolved_budget:
            values["budget_id"] = resolved_budget.id

    # Handle type marking
    if rule.target_transaction_type is not None:
        values["transaction_type"] = rule.target_transaction_type
        values["exclude_from_budget"] = rule.target_exclude_from_budget

    return values


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

        matched_ids: set[int] = set()
        for transaction in transactions:
            matched_rule = next(
                (
                    r
                    for r in rules
                    if _should_process_transaction(
                        transaction, r, matched_ids, override_existing,
                    )
                    and matches_all_conditions(transaction, r.conditions)
                ),
                None,
            )

            if not matched_rule:
                skipped_count += 1
                continue

            matched_ids.add(transaction.id)

            update_values = await _resolve_update_values(
                user_id,
                transaction,
                matched_rule,
                resolved_budgets,
                sess,
            )

            if not update_values:
                skipped_count += 1
                continue

            try:
                await sess.execute(
                    update(SimpleFinTransaction)
                    .where(SimpleFinTransaction.id == transaction.id)
                    .values(**update_values),
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
