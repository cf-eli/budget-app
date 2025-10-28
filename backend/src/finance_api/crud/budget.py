"""Budget CRUD operations."""

from calendar import monthrange
from datetime import UTC, datetime

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from finance_api.models.budget import Budget, Expense, Fund, Income
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction, TransactionLineItem


async def create_budget(
    user_id: int,
    name: str,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> int:
    """Create a budget entry and return the budget ID."""
    now = datetime.now(UTC)
    if month is None:
        month = now.month
    if year is None:
        year = now.year
    async with get_session(session) as sess:
        stmt = (
            insert(Budget)
            .values(user_id=user_id, name=name, month=month, year=year)
            .returning(Budget.id)
        )
        result = await sess.execute(stmt)
        await sess.commit()
        return result.scalar_one()


async def create_income(
    user_id: int,
    name: str,
    fixed: bool,
    expected_amount: float | None,
    min_amount: float | None,
    max_amount: float | None,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> None:
    """Create a budget with income details."""
    # Create budget first
    budget_id = await create_budget(
        user_id,
        name,
        month=month,
        year=year,
        session=session,
    )

    # Create income entry linked to budget
    async with get_session(session) as sess:
        stmt = insert(Income).values(
            id=budget_id,
            fixed=fixed,
            expected_amount=expected_amount,
            min=min_amount,
            max=max_amount,
        )
        await sess.execute(stmt)
        await sess.commit()


async def create_expense(
    user_id: int,
    name: str,
    fixed: bool,
    flexible: bool,
    expected_amount: float | None,
    min_amount: float | None,
    max_amount: float | None,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> None:
    """Create a budget with expense details."""
    budget_id = await create_budget(
        user_id,
        name,
        month=month,
        year=year,
        session=session,
    )

    async with get_session(session) as sess:
        stmt = insert(Expense).values(
            id=budget_id,
            fixed=fixed,
            flexible=flexible,
            expected_amount=expected_amount,
            min=min_amount,
            max=max_amount,
        )
        await sess.execute(stmt)
        await sess.commit()


async def create_fund(
    user_id: int,
    name: str,
    priority: int | None,
    increment: float | None,
    current_amount: float = 0.0,
    max_amount: float | None = None,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> None:
    """Create a budget with fund details."""
    budget_id = await create_budget(
        user_id,
        name,
        month=month,
        year=year,
        session=session,
    )

    async with get_session(session) as sess:
        stmt = insert(Fund).values(
            id=budget_id,
            priority=priority,
            increment=increment,
            current_amount=current_amount,
            max=max_amount,
        )
        await sess.execute(stmt)
        await sess.commit()


async def get_budgets(
    user_id: int,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> dict:
    """
    Get all budgets for a user with transaction sums (accounting for line items).

    Args:
        user_id: User ID
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year
        session: Optional database session. If None, creates a new session.

    """
    income_alias = aliased(Income)
    expense_alias = aliased(Expense)
    fund_alias = aliased(Fund)

    # Use current month/year if not provided
    now = datetime.now(UTC)
    if month is None:
        month = now.month
    if year is None:
        year = now.year

    # Get all budget sums at once (optimized, includes line items)
    budget_sums = await get_all_budget_sums_with_line_items(
        month=month,
        year=year,
        session=session,
    )

    # Get carryover amounts
    carryover_by_name = await get_carryover_for_budgets(
        user_id=user_id,
        month=month,
        year=year,
        session=session,
    )

    query = (
        select(
            Budget.id.label("budget_id"),
            Budget.user_id,
            Budget.name,
            Budget.enable,
            Budget.deleted,
            income_alias.id.label("income_id"),
            income_alias.fixed.label("income_fixed"),
            income_alias.expected_amount.label("income_expected_amount"),
            income_alias.min.label("income_min"),
            income_alias.max.label("income_max"),
            expense_alias.id.label("expense_id"),
            expense_alias.flexible.label("expense_flexible"),
            expense_alias.fixed.label("expense_fixed"),
            expense_alias.expected_amount.label("expense_expected_amount"),
            expense_alias.min.label("expense_min"),
            expense_alias.max.label("expense_max"),
            fund_alias.id.label("fund_id"),
            fund_alias.priority.label("fund_priority"),
            fund_alias.increment.label("fund_increment"),
            fund_alias.current_amount.label("fund_current_amount"),
            fund_alias.max.label("fund_max"),
        )
        .where(Budget.user_id == user_id)
        .where(Budget.month == month)
        .where(Budget.year == year)
        .outerjoin(income_alias, Budget.id == income_alias.id)
        .outerjoin(expense_alias, Budget.id == expense_alias.id)
        .outerjoin(fund_alias, Budget.id == fund_alias.id)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        rows = result.all()

    incomes = []
    expenses = []
    flexibles = []
    funds = []

    for row in rows:
        row_dict = row._mapping  # noqa: SLF001
        budget_id = row_dict["budget_id"]
        budget_name = row_dict["name"]
        transaction_sum = budget_sums.get(budget_id, 0.0)
        carryover = carryover_by_name.get(budget_name, 0.0)

        budget_info = {
            "id": budget_id,
            "user_id": row_dict["user_id"],
            "name": budget_name,
            "enable": row_dict["enable"],
            "deleted": row_dict["deleted"],
            "transaction_sum": float(transaction_sum),
            "carryover": float(carryover),
        }

        if row_dict["income_id"] is not None:
            incomes.append(
                {
                    **budget_info,
                    "fixed": row_dict["income_fixed"],
                    "expected_amount": row_dict["income_expected_amount"],
                    "min": row_dict["income_min"],
                    "max": row_dict["income_max"],
                    "amount_after_transactions": row_dict["income_expected_amount"]
                    + transaction_sum,
                },
            )
        elif row_dict["expense_id"] is not None:
            expense_data = {
                **budget_info,
                "fixed": row_dict["expense_fixed"],
                "expected_amount": row_dict["expense_expected_amount"],
                "min": row_dict["expense_min"],
                "max": row_dict["expense_max"],
                # For expenses, transaction_sum is negative, so subtract from expected
                "amount_after_transactions": row_dict["expense_expected_amount"]
                + transaction_sum,
            }
            if row_dict["expense_flexible"]:
                flexibles.append(expense_data)
            else:
                expenses.append(expense_data)
        elif row_dict["fund_id"] is not None:
            funds.append(
                {
                    **budget_info,
                    "priority": row_dict["fund_priority"],
                    "increment": row_dict["fund_increment"],
                    "current_amount": row_dict["fund_current_amount"],
                    "max": row_dict["fund_max"],
                    "amount_after_transactions": row_dict["fund_current_amount"]
                    + transaction_sum,
                },
            )

    return {
        "incomes": incomes,
        "expenses": expenses,
        "flexibles": flexibles,
        "funds": funds,
    }


async def get_income_sum(user_id: int, session: AsyncSession | None = None) -> float:
    """Get total income for a user."""
    query = (
        select(func.sum(SimpleFinTransaction.amount))
        .select_from(Budget)
        .join(Income, Budget.id == Income.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(SimpleFinTransaction.amount > 0)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return result.scalar() or 0.0


async def get_expense_sum(user_id: int, session: AsyncSession | None = None) -> float:
    """Get total fixed expenses for a user."""
    query = (
        select(func.sum(func.abs(SimpleFinTransaction.amount)))
        .select_from(Budget)
        .join(Expense, Budget.id == Expense.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(~Expense.flexible)
        .where(SimpleFinTransaction.amount < 0)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return result.scalar() or 0.0


async def get_flexible_sum(user_id: int, session: AsyncSession | None = None) -> float:
    """Get total flexible expenses for a user."""
    query = (
        select(func.sum(func.abs(SimpleFinTransaction.amount)))
        .select_from(Budget)
        .join(Expense, Budget.id == Expense.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(Expense.flexible)
        .where(SimpleFinTransaction.amount < 0)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return result.scalar() or 0.0


async def get_fund_sum(user_id: int, session: AsyncSession | None = None) -> float:
    """Get total funds allocated for a user."""
    query = (
        select(func.sum(Fund.current_amount))
        .select_from(Budget)
        .join(Fund, Budget.id == Fund.id)
        .where(Budget.user_id == user_id)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return result.scalar() or 0.0


async def get_budgets_name(
    user_id: int,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> list[dict]:
    """
    Get all budget IDs and names for a specific user.

    Args:
        user_id: User ID
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year
        session: Optional database session. If None, creates a new session.

    """
    # Use current month/year if not provided
    now = datetime.now(UTC)
    if month is None:
        month = now.month
    if year is None:
        year = now.year

    query = (
        select(Budget.id, Budget.name)
        .where(Budget.user_id == user_id)
        .where(Budget.month == month)
        .where(Budget.year == year)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return [dict(row._mapping) for row in result.all()]  # noqa: SLF001


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

    Carryover is the sum of transaction_sum (current activity) from all
    previous months for budgets with the same name. Returns dict with
    budget names as keys.

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

            carryover_by_name[budget_name] += unsplit_sum + split_sum

        return carryover_by_name


async def copy_budgets_from_previous_month(
    user_id: int,
    target_month: int,
    target_year: int,
    source_month: int | None = None,
    source_year: int | None = None,
    session: AsyncSession | None = None,
) -> dict:
    """
    Copy all budgets from source month to target month.

    Args:
        user_id: User ID
        target_month: Target month (1-12)
        target_year: Target year (e.g., 2024)
        source_month: Optional source month (defaults to previous month)
        source_year: Optional source year (defaults based on source_month)
        session: Optional database session

    Returns:
        Dict with counts of copied budgets and source month/year

    Raises:
        ValueError: If target month already has budgets or no source month found

    """
    # Calculate source month and year if not provided
    if source_month is None or source_year is None:
        # Default to previous month
        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

    # Use provided source_month/year (for copying from next month in past scenarios)
    prev_month = source_month
    prev_year = source_year

    async with get_session(session) as sess:
        # Check if target month already has budgets
        target_check = (
            select(Budget.id)
            .where(Budget.user_id == user_id)
            .where(Budget.month == target_month)
            .where(Budget.year == target_year)
            .limit(1)
        )
        target_result = await sess.execute(target_check)
        if target_result.scalar_one_or_none() is not None:
            msg = f"Target month {target_month}/{target_year} already has budgets"
            raise ValueError(msg)

        # Get all budgets from previous month
        prev_budgets_query = (
            select(
                Budget.id,
                Budget.name,
                Budget.enable,
                Budget.deleted,
                Income.id.label("income_id"),
                Income.fixed.label("income_fixed"),
                Income.expected_amount.label("income_expected"),
                Income.min.label("income_min"),
                Income.max.label("income_max"),
                Expense.id.label("expense_id"),
                Expense.fixed.label("expense_fixed"),
                Expense.flexible.label("expense_flexible"),
                Expense.expected_amount.label("expense_expected"),
                Expense.min.label("expense_min"),
                Expense.max.label("expense_max"),
                Fund.id.label("fund_id"),
                Fund.priority.label("fund_priority"),
                Fund.increment.label("fund_increment"),
                Fund.max.label("fund_max"),
            )
            .where(Budget.user_id == user_id)
            .where(Budget.month == prev_month)
            .where(Budget.year == prev_year)
            .outerjoin(Income, Budget.id == Income.id)
            .outerjoin(Expense, Budget.id == Expense.id)
            .outerjoin(Fund, Budget.id == Fund.id)
        )

        prev_result = await sess.execute(prev_budgets_query)
        prev_budgets = prev_result.all()

        if not prev_budgets:
            msg = f"No budgets found in previous month {prev_month}/{prev_year}"
            raise ValueError(msg)

        # Track counts
        counts = {"income": 0, "expense": 0, "flexible": 0, "fund": 0}

        # Copy each budget
        for row in prev_budgets:
            row_dict = row._mapping  # noqa: SLF001

            # Create new budget
            new_budget_stmt = (
                insert(Budget)
                .values(
                    user_id=user_id,
                    name=row_dict["name"],
                    enable=row_dict["enable"],
                    deleted=row_dict["deleted"],
                    month=target_month,
                    year=target_year,
                )
                .returning(Budget.id)
            )
            new_budget_result = await sess.execute(new_budget_stmt)
            new_budget_id = new_budget_result.scalar_one()

            # Copy income details if exists
            if row_dict["income_id"] is not None:
                income_stmt = insert(Income).values(
                    id=new_budget_id,
                    fixed=row_dict["income_fixed"],
                    expected_amount=row_dict["income_expected"],
                    min=row_dict["income_min"],
                    max=row_dict["income_max"],
                )
                await sess.execute(income_stmt)
                counts["income"] += 1

            # Copy expense details if exists
            elif row_dict["expense_id"] is not None:
                expense_stmt = insert(Expense).values(
                    id=new_budget_id,
                    fixed=row_dict["expense_fixed"],
                    flexible=row_dict["expense_flexible"],
                    expected_amount=row_dict["expense_expected"],
                    min=row_dict["expense_min"],
                    max=row_dict["expense_max"],
                )
                await sess.execute(expense_stmt)
                if row_dict["expense_flexible"]:
                    counts["flexible"] += 1
                else:
                    counts["expense"] += 1

            # Copy fund details if exists
            elif row_dict["fund_id"] is not None:
                fund_stmt = insert(Fund).values(
                    id=new_budget_id,
                    priority=row_dict["fund_priority"],
                    increment=row_dict["fund_increment"],
                    current_amount=0.0,  # Reset current amount for new month
                    max=row_dict["fund_max"],
                )
                await sess.execute(fund_stmt)
                counts["fund"] += 1

        # Commit all changes
        await sess.commit()

        return {
            "message": "Successfully copied budgets",
            "copied_budgets": counts,
            "source_month": prev_month,
            "source_year": prev_year,
        }
