"""Budget copy operations."""

from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Expense, Fund, FundMaster, Income
from finance_api.models.db import get_session


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
                # Get previous fund's master and check if it has balance
                prev_fund_query = (
                    select(
                        Fund.master_fund_id,
                        Fund.month_amount,
                        FundMaster.total_amount,
                    )
                    .join(FundMaster, Fund.master_fund_id == FundMaster.id)
                    .where(Fund.id == row_dict["fund_id"])
                )
                prev_fund_result = await sess.execute(prev_fund_query)
                prev_fund_data = prev_fund_result.first()

                master_fund_id = prev_fund_data.master_fund_id

                fund_stmt = insert(Fund).values(
                    id=new_budget_id,
                    priority=row_dict["fund_priority"],
                    increment=row_dict["fund_increment"],
                    month_amount=Decimal("0.00"),  # Reset for new month
                    max=row_dict["fund_max"],
                    master_fund_id=master_fund_id,
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


# Fund Master Operations
