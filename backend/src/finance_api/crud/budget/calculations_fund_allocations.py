"""
Fund allocation operations.

Functions for allocating carryover to funds and applying fund increments.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund, FundMaster
from finance_api.models.db import get_session

from .calculations_fund import calculate_fund_balance
from .queries import get_budgets


async def apply_fund_increments(
    user_id: int,
    month: int,
    year: int,
    safe_mode: bool = False,
    session: AsyncSession | None = None,
) -> dict:
    """
    Apply fund increments to funds in the specified month.

    With the master fund system:
    1. Adds each fund's increment to its month_amount
    2. Updates the master_fund.total_amount by the same increment
    3. No propagation needed (master tracks cumulative balance)

    Args:
        user_id: User ID
        month: Month (1-12)
        year: Year (e.g., 2024)
        safe_mode: If True, stops allocation before balance goes negative
        session: Optional database session

    Returns:
        Dict with:
            - applied_funds: List of {fund_id, fund_name, amount_added,
              new_master_balance}
            - skipped_funds: List of {fund_id, fund_name, reason}
            - balance_before: Balance before applying funds
            - balance_after: Balance after applying funds
            - total_applied: Total amount added to funds

    """
    async with get_session(session) as sess:
        # Get current balance for the month
        budgets_data = await get_budgets(user_id, month, year, session=sess)

        total_income = sum(
            income["transaction_sum"] for income in budgets_data["incomes"]
        )
        total_expenses = sum(
            expense["transaction_sum"] for expense in budgets_data["expenses"]
        )
        total_flexible = sum(
            flexible["transaction_sum"] for flexible in budgets_data["flexibles"]
        )

        # Include carryover from all budget types
        total_carryover = (
            sum(income["carryover"] for income in budgets_data["incomes"])
            + sum(expense["carryover"] for expense in budgets_data["expenses"])
            + sum(flexible["carryover"] for flexible in budgets_data["flexibles"])
            + sum(fund["carryover"] for fund in budgets_data["funds"])
        )

        # Current month fund allocations
        total_funds = sum(fund["month_amount"] for fund in budgets_data["funds"])

        balance_before = (
            Decimal(str(total_income))
            + Decimal(str(total_expenses))  # expenses are negative
            + Decimal(str(total_flexible))  # flexibles are negative
            + Decimal(str(total_carryover))
            - Decimal(str(total_funds))
        )

        # Get all funds for the month, sorted by priority
        funds_query = (
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
            .where(Budget.user_id == user_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
            .where(Budget.enable == True)  # noqa: E712
            .order_by(Fund.priority.asc(), Fund.id.asc())
        )
        funds_result = await sess.execute(funds_query)
        funds = funds_result.all()

        applied_funds = []
        skipped_funds = []
        total_applied = Decimal("0.00")
        remaining_balance = balance_before

        for fund in funds:
            # Skip if increment is 0
            if fund.increment == 0:
                skipped_funds.append(
                    {
                        "fund_id": fund.id,
                        "fund_name": fund.name,
                        "reason": "Increment is 0",
                    },
                )
                continue

            # Check max limit if exists
            amount_to_add = fund.increment
            if fund.max is not None:
                # Get current master balance
                balance_info = await calculate_fund_balance(fund.id, session=sess)
                current_balance = Decimal(str(balance_info["master_balance"]))
                room_to_max = fund.max - current_balance

                if room_to_max <= 0:
                    skipped_funds.append(
                        {
                            "fund_id": fund.id,
                            "fund_name": fund.name,
                            "reason": "Fund has reached maximum",
                        },
                    )
                    continue
                amount_to_add = min(amount_to_add, room_to_max)

            # In safe mode, check if this would make balance negative
            if safe_mode and (remaining_balance - amount_to_add) < 0:
                amount_to_add = max(Decimal("0.00"), remaining_balance)
                if amount_to_add == 0:
                    skipped_funds.append(
                        {
                            "fund_id": fund.id,
                            "fund_name": fund.name,
                            "reason": "Insufficient balance (safe mode)",
                        },
                    )
                    continue

            # Update fund's month_amount
            update_fund_stmt = select(Fund).where(Fund.id == fund.id)
            update_fund_result = await sess.execute(update_fund_stmt)
            fund_obj = update_fund_result.scalar_one()
            fund_obj.month_amount += amount_to_add

            # Update master fund's total_amount
            update_master_stmt = select(FundMaster).where(
                FundMaster.id == fund.master_fund_id,
            )
            update_master_result = await sess.execute(update_master_stmt)
            master_obj = update_master_result.scalar_one()
            master_obj.total_amount += amount_to_add

            applied_funds.append(
                {
                    "fund_id": fund.id,
                    "fund_name": fund.name,
                    "amount_added": float(amount_to_add),
                    "new_master_balance": float(master_obj.total_amount),
                },
            )

            total_applied += amount_to_add
            remaining_balance -= amount_to_add

        await sess.commit()

        return {
            "applied_funds": applied_funds,
            "skipped_funds": skipped_funds,
            "balance_before": float(balance_before),
            "balance_after": float(remaining_balance),
            "total_applied": float(total_applied),
            "would_go_negative": remaining_balance < 0,
        }
