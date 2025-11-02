"""
Fund calculation operations.

Functions for calculating fund balances and master fund operations.
These operations focus on fund entities and their complex interdependencies.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund, FundMaster
from finance_api.models.db import get_session

from .calculations_budget import get_budget_sum_with_line_items


async def calculate_fund_balance(
    fund_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Calculate fund balance using master fund system.

    Balance = dynamically calculated master balance from all funds

    This is much simpler than the old chain-traversal approach as the master
    tracks cumulative balance across all linked funds.

    Args:
        fund_id: ID of the fund to calculate balance for
        session: Optional database session

    Returns:
        Dict with balance breakdown and calculation details

    """
    async with get_session(session) as sess:
        # Get fund and its master
        fund_query = (
            select(
                Fund.id,
                Fund.master_fund_id,
                Fund.month_amount,
                FundMaster.name.label("master_name"),
                Budget.name,
                Budget.month,
                Budget.year,
            )
            .join(FundMaster, Fund.master_fund_id == FundMaster.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.id == fund_id)
        )
        fund_result = await sess.execute(fund_query)
        fund_data = fund_result.first()

        if not fund_data:
            return {
                "total_balance": 0.0,
                "master_balance": 0.0,
                "transactions": 0.0,
                "breakdown": [],
            }

        # Use dynamically calculated master balance instead of stored total_amount
        master_balance = await calculate_master_balance(
            fund_data.master_fund_id,
            sess,
        )

        # Get all fund IDs that share this master
        master_funds_query = select(Fund.id).where(
            Fund.master_fund_id == fund_data.master_fund_id,
        )
        master_funds_result = await sess.execute(master_funds_query)
        all_fund_ids = [row[0] for row in master_funds_result.all()]

        # Calculate total transactions across all funds sharing this master
        total_transactions = Decimal("0.00")
        for fid in all_fund_ids:
            transaction_sum = await get_budget_sum_with_line_items(fid, session=sess)
            total_transactions += Decimal(str(transaction_sum))

        # Total balance = calculated master balance
        # (Note: master_balance already includes transactions via
        # calculate_master_balance)
        total_balance = Decimal(str(master_balance))

        return {
            "total_balance": float(total_balance),
            "master_balance": float(master_balance),
            "transactions": float(total_transactions),
            "breakdown": [
                {
                    "fund_id": fund_data.id,
                    "fund_name": fund_data.name,
                    "month": fund_data.month,
                    "year": fund_data.year,
                    "master_id": fund_data.master_fund_id,
                    "master_name": fund_data.master_name,
                    "master_balance": float(master_balance),
                    "transactions": float(total_transactions),
                },
            ],
        }


async def calculate_master_balance(
    master_fund_id: int,
    session: AsyncSession,
) -> float:
    """
    Calculate the actual master fund balance from all funds linked to this master.

    Formula: sum(month_amount + transaction_sum) for all funds with this master_fund_id

    This is the source of truth for master balance, rather than FundMaster.total_amount
    which can drift over time.

    Args:
        master_fund_id: Master fund ID
        session: Database session

    Returns:
        Calculated master balance

    """
    # Get all funds for this master
    funds_query = select(Fund.id, Fund.month_amount).where(
        Fund.master_fund_id == master_fund_id,
    )
    funds_result = await session.execute(funds_query)
    funds = funds_result.all()

    total_balance = 0.0
    for fund in funds:
        # Get transaction sum for this fund
        transaction_sum = await get_budget_sum_with_line_items(
            fund.id,
            session=session,
        )
        total_balance += float(fund.month_amount) + transaction_sum

    return total_balance
