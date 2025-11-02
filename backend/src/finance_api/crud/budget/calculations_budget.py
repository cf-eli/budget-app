"""
Budget calculation operations.

Functions for calculating budget sums, line items, and carryover.
These operations focus on budget entities (income, expense, flexible).
"""

from calendar import monthrange
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction, TransactionLineItem


async def get_budget_sum_with_line_items(
    budget_id: int,
    session: AsyncSession | None = None,
) -> float:
    """
    Get budget sum including line items.

    If a transaction is split, use line items; otherwise use parent transaction.
    """
    async with get_session(session) as sess:
        # Sum from transactions that aren't split
        unsplit_query = (
            select(func.sum(SimpleFinTransaction.amount))
            .where(SimpleFinTransaction.budget_id == budget_id)
            .where(~SimpleFinTransaction.is_split)
        )
        unsplit_result = await sess.execute(unsplit_query)
        unsplit_sum = unsplit_result.scalar() or 0.0

        # Sum from line items where parent is split
        split_query = select(func.sum(TransactionLineItem.amount)).where(
            TransactionLineItem.budget_id == budget_id,
        )
        split_result = await sess.execute(split_query)
        split_sum = split_result.scalar() or 0.0

        return unsplit_sum + split_sum


async def get_all_budget_sums_with_line_items(
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> dict[int, float]:
    """
    Get all budget sums at once (optimized for get_budgets query).

    Returns dict of {budget_id: total_amount}.

    Args:
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year
        session: Optional database session. If None, creates a new session.

    """
    async with get_session(session) as sess:
        # Use current month/year if not provided
        now = datetime.now(UTC)
        if month is None:
            month = now.month
        if year is None:
            year = now.year

        # Calculate start and end dates for the month/year
        month_start = datetime(year, month, 1, tzinfo=UTC)
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        # Sum unsplit transactions grouped by budget
        unsplit_query = (
            select(
                SimpleFinTransaction.budget_id,
                func.sum(SimpleFinTransaction.amount).label("total"),
            )
            .where(SimpleFinTransaction.budget_id.isnot(None))
            .where(~SimpleFinTransaction.is_split)
            .where(SimpleFinTransaction.transacted_at >= month_start)
            .where(SimpleFinTransaction.transacted_at <= month_end)
            .group_by(SimpleFinTransaction.budget_id)
        )
        unsplit_result = await sess.execute(unsplit_query)
        unsplit_sums = {row.budget_id: row.total for row in unsplit_result}

        # Sum line items grouped by budget
        # (need to join with parent transaction for date)
        split_query = (
            select(
                TransactionLineItem.budget_id,
                func.sum(TransactionLineItem.amount).label("total"),
            )
            .join(
                SimpleFinTransaction,
                TransactionLineItem.parent_transaction_id == SimpleFinTransaction.id,
            )
            .where(TransactionLineItem.budget_id.isnot(None))
            .where(SimpleFinTransaction.transacted_at >= month_start)
            .where(SimpleFinTransaction.transacted_at <= month_end)
            .group_by(TransactionLineItem.budget_id)
        )
        split_result = await sess.execute(split_query)
        split_sums = {row.budget_id: row.total for row in split_result}

        # Combine both
        all_budget_ids = set(unsplit_sums.keys()) | set(split_sums.keys())
        combined = {}
        for budget_id in all_budget_ids:
            combined[budget_id] = unsplit_sums.get(budget_id, 0.0) + split_sums.get(
                budget_id,
                0.0,
            )

        return combined


async def get_carryover_for_budgets(
    user_id: int,
    month: int,
    year: int,
    session: AsyncSession | None = None,
) -> dict[str, float]:
    """
    Calculate carryover amounts for budgets based on previous months.

    Carryover represents the cumulative balance from all previous months.

    Formula by budget type:
    - Income/Expense/Flexible: carryover = sum(transaction_sum for all previous months)
    - Funds: carryover = sum(-month_amount for all previous months)
      * month_amount = allocations to the fund (positive values)
      * Fund transactions are IGNORED - they only affect master fund balance
      * Only the allocation reduces available budget balance

    Current month balance formula (applied in frontend):
    balance = income + expenses + flexibles + carryover - current_month_funds

    This ensures:
    - Previous month's ending balance = next month's carryover
    - Fund allocations reduce available balance
    - Fund transactions (withdrawals/deposits) ONLY affect master balance,
      not budget balance

    Args:
        user_id: User ID
        month: Current month (1-12)
        year: Current year (e.g., 2024)
        session: Optional database session

    Returns:
        Dict of {budget_name: carryover_amount}

    """
    async with get_session(session) as sess:
        # Get all budgets for current month/year to get their names
        current_budgets_query = (
            select(Budget.id, Budget.name)
            .where(Budget.user_id == user_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
        )
        current_budgets_result = await sess.execute(current_budgets_query)
        current_budgets = {row.id: row.name for row in current_budgets_result}

        if not current_budgets:
            return {}

        # Get all previous budgets with same names
        budget_names = list(set(current_budgets.values()))

        # Get all previous budgets (before current month/year)
        # Create comparison date for the start of current month
        current_month_start = datetime(year, month, 1, tzinfo=UTC)

        previous_budgets_query = (
            select(Budget.id, Budget.name, Budget.month, Budget.year)
            .where(Budget.user_id == user_id)
            .where(Budget.name.in_(budget_names))
        )
        previous_budgets_result = await sess.execute(previous_budgets_query)
        previous_budgets = []
        for row in previous_budgets_result:
            budget_month_start = datetime(row.year, row.month, 1, tzinfo=UTC)
            # Only include budgets from before current month
            if budget_month_start < current_month_start:
                previous_budgets.append((row.id, row.name, row.month, row.year))

        if not previous_budgets:
            return dict.fromkeys(budget_names, 0.0)

        # Get transaction sums for all previous budgets
        carryover_by_name = dict.fromkeys(budget_names, 0.0)

        for budget_id, budget_name, prev_month, prev_year in previous_budgets:
            # Get transaction sum for this previous budget
            last_day = monthrange(prev_year, prev_month)[1]
            prev_month_start = datetime(prev_year, prev_month, 1, tzinfo=UTC)
            prev_month_end = datetime(
                prev_year,
                prev_month,
                last_day,
                23,
                59,
                59,
                999999,
                tzinfo=UTC,
            )

            # Sum unsplit transactions for this budget
            unsplit_query = (
                select(func.sum(SimpleFinTransaction.amount))
                .where(SimpleFinTransaction.budget_id == budget_id)
                .where(~SimpleFinTransaction.is_split)
                .where(SimpleFinTransaction.transacted_at >= prev_month_start)
                .where(SimpleFinTransaction.transacted_at <= prev_month_end)
            )
            unsplit_result = await sess.execute(unsplit_query)
            unsplit_sum = unsplit_result.scalar() or 0.0

            # Sum line items for this budget
            split_query = (
                select(func.sum(TransactionLineItem.amount))
                .join(
                    SimpleFinTransaction,
                    TransactionLineItem.parent_transaction_id
                    == SimpleFinTransaction.id,
                )
                .where(TransactionLineItem.budget_id == budget_id)
                .where(SimpleFinTransaction.transacted_at >= prev_month_start)
                .where(SimpleFinTransaction.transacted_at <= prev_month_end)
            )
            split_result = await sess.execute(split_query)
            split_sum = split_result.scalar() or 0.0

            transaction_sum = unsplit_sum + split_sum

            # Check if this is a fund
            fund_query = select(Fund.month_amount).where(Fund.id == budget_id)
            fund_result = await sess.execute(fund_query)
            fund_month_amount = fund_result.scalar()

            if fund_month_amount is not None:
                # This is a fund
                # Fund carryover = -month_amount (allocation reduces available balance)
                # Fund transactions are IGNORED - they only affect master balance
                carryover_by_name[budget_name] += -float(fund_month_amount)
            else:
                # Non-fund budget: carryover = transactions
                carryover_by_name[budget_name] += transaction_sum

        return carryover_by_name
