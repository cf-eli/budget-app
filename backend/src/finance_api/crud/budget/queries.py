"""Budget query operations."""

from datetime import UTC, datetime

from litestar.exceptions import NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from finance_api.models.budget import Budget, Expense, Fund, FundMaster, Income
from finance_api.models.db import get_session

from .calculations_budget import (
    get_all_budget_sums_with_line_items,
    get_budget_sum_with_line_items,
    get_carryover_for_budgets,
)
from .calculations_fund import calculate_master_balance


async def get_fund_by_id(
    fund_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Get fund details by ID.

    Args:
        fund_id: The fund ID
        session: Optional database session

    Returns:
        Dict with fund details including:
        - id, name, priority, increment, max, month_amount, master_fund_id

    Raises:
        NotFoundException: If fund not found

    """
    async with get_session(session) as sess:
        fund_query = (
            select(
                Fund.id,
                Fund.priority,
                Fund.increment,
                Fund.max,
                Fund.month_amount,
                Fund.master_fund_id,
                Budget.name,
            )
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.id == fund_id)
        )
        result = await sess.execute(fund_query)
        fund_data = result.first()

        if not fund_data:
            msg = f"Fund {fund_id} not found"
            raise NotFoundException(msg)

        return {
            "id": fund_data.id,
            "name": fund_data.name,
            "priority": fund_data.priority,
            "increment": fund_data.increment,
            "max": fund_data.max,
            "month_amount": fund_data.month_amount,
            "master_fund_id": fund_data.master_fund_id,
        }


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
            fund_alias.master_fund_id.label("fund_master_fund_id"),
            fund_alias.month_amount.label("fund_month_amount"),
            fund_alias.max.label("fund_max"),
            FundMaster.total_amount.label("fund_master_balance"),
            FundMaster.name.label("fund_master_name"),
        )
        .where(Budget.user_id == user_id)
        .where(Budget.month == month)
        .where(Budget.year == year)
        .outerjoin(income_alias, Budget.id == income_alias.id)
        .outerjoin(expense_alias, Budget.id == expense_alias.id)
        .outerjoin(fund_alias, Budget.id == fund_alias.id)
        .outerjoin(FundMaster, fund_alias.master_fund_id == FundMaster.id)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        rows = result.all()

        # Calculate actual master balances dynamically from all funds
        # Get unique master_fund_ids from the results
        master_fund_ids = {
            row._mapping["fund_master_fund_id"]  # noqa: SLF001
            for row in rows
            if row._mapping["fund_master_fund_id"] is not None  # noqa: SLF001
        }

        # Calculate balance for each master
        master_balances = {}
        for master_id in master_fund_ids:
            master_balances[master_id] = await calculate_master_balance(
                master_id,
                sess,
            )

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
            master_fund_id = row_dict["fund_master_fund_id"]
            month_amount = row_dict["fund_month_amount"] or 0
            master_name = row_dict.get("fund_master_name")
            # Use calculated master balance instead of stored total_amount
            master_balance = master_balances.get(master_fund_id, 0.0)
            funds.append(
                {
                    **budget_info,
                    "priority": row_dict["fund_priority"],
                    "increment": row_dict["fund_increment"],
                    "master_balance": float(master_balance),
                    "master_fund_id": master_fund_id,
                    "master_fund_name": master_name,
                    "month_amount": float(month_amount),
                    "max": row_dict["fund_max"],
                    # Use month_amount (monthly contribution) not master_balance
                    "amount_after_transactions": float(month_amount) + transaction_sum,
                },
            )

    return {
        "incomes": incomes,
        "expenses": expenses,
        "flexibles": flexibles,
        "funds": funds,
    }


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

    Returns:
        List of dicts with id, name, and master_id (for funds only)

    """
    # Use current month/year if not provided
    now = datetime.now(UTC)
    if month is None:
        month = now.month
    if year is None:
        year = now.year

    query = (
        select(Budget.id, Budget.name, Fund.master_fund_id)
        .outerjoin(Fund, Budget.id == Fund.id)
        .where(Budget.user_id == user_id)
        .where(Budget.month == month)
        .where(Budget.year == year)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return [
            {"id": row.id, "name": row.name, "master_id": row.master_fund_id}
            for row in result.all()
        ]


async def get_master_fund_details(
    master_id: int,
    user_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Get master fund details with all associated funds and their contributions.

    Args:
        master_id: Master fund ID
        user_id: User ID (for authorization check)
        session: Optional database session

    Returns:
        Dict with master fund details and list of all funds

    Raises:
        ValueError: If master not found or user doesn't own funds

    """
    async with get_session(session) as sess:
        # Get master fund
        master_stmt = select(FundMaster).where(FundMaster.id == master_id)
        master_result = await sess.execute(master_stmt)
        master = master_result.scalar_one_or_none()

        if not master:
            msg = f"Master fund {master_id} not found"
            raise NotFoundException(msg)

        # Get all funds linked to this master with their details
        funds_query = (
            select(
                Fund.id.label("fund_id"),
                Budget.name.label("budget_name"),
                Budget.month,
                Budget.year,
                Fund.month_amount,
                Budget.user_id,
            )
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.master_fund_id == master_id)
            .order_by(Budget.year.asc(), Budget.month.asc())
        )
        funds_result = await sess.execute(funds_query)
        funds_data = funds_result.all()

        if not funds_data:
            # Master exists but has no funds - calculate balance (should be 0)
            calculated_balance = await calculate_master_balance(master_id, sess)
            return {
                "master_id": master_id,
                "master_name": master.name,
                "total_balance": calculated_balance,
                "funds": [],
            }

        # Verify user owns these funds
        if funds_data and funds_data[0].user_id != user_id:
            msg = f"User {user_id} does not own funds in master {master_id}"
            raise ValueError(msg)

        # Get transaction sums for each fund
        funds_list = []
        for fund_data in funds_data:
            # Get transaction sum for this fund (including line items)
            transaction_sum = await get_budget_sum_with_line_items(
                fund_data.fund_id,
                session=sess,
            )

            net_contribution = float(fund_data.month_amount) + transaction_sum

            funds_list.append(
                {
                    "fund_id": fund_data.fund_id,
                    "budget_name": fund_data.budget_name,
                    "month": fund_data.month,
                    "year": fund_data.year,
                    "month_amount": float(fund_data.month_amount),
                    "transactions": transaction_sum,
                    "net_contribution": net_contribution,
                },
            )

        # Use calculated master balance instead of stored total_amount
        calculated_balance = await calculate_master_balance(master_id, sess)

        return {
            "master_id": master_id,
            "master_name": master.name,
            "total_balance": calculated_balance,
            "funds": funds_list,
        }
