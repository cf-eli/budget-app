"""
Orphaned fund master management.

Functions for managing orphaned fund masters - those without active funds.
Includes finding, discontinuing, and re-linking orphaned masters.
"""

from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund, FundMaster
from finance_api.models.db import get_session

from .base import create_budget


async def get_orphaned_fund_masters(
    user_id: int,
    month: int,
    year: int,
    session: AsyncSession | None = None,
) -> list[dict]:
    """
    Get fund masters with balance > 0 but no fund for the specified month.

    These are "orphaned" funds that need attention - either add to current
    month or discontinue to return balance to budget.

    Args:
        user_id: User ID
        month: Month to check (1-12)
        year: Year to check
        session: Optional database session

    Returns:
        List of dicts with orphaned master info

    """
    async with get_session(session) as sess:
        # Get all masters with balance > 0 for this user's funds
        masters_query = (
            select(
                FundMaster.id,
                FundMaster.name,
                FundMaster.total_amount,
                FundMaster.created_at,
            )
            .join(Fund, FundMaster.id == Fund.master_fund_id)
            .join(Budget, Fund.id == Budget.id)
            .where(Budget.user_id == user_id)
            .where(FundMaster.total_amount > 0)
            .distinct()
        )
        masters_result = await sess.execute(masters_query)
        all_masters = masters_result.all()

        orphaned_masters = []

        for master in all_masters:
            # Check if this master has a fund for the specified month
            fund_exists_query = (
                select(Fund.id)
                .join(Budget, Fund.id == Budget.id)
                .where(Fund.master_fund_id == master.id)
                .where(Budget.month == month)
                .where(Budget.year == year)
                .limit(1)
            )
            fund_exists_result = await sess.execute(fund_exists_query)
            has_fund_this_month = fund_exists_result.scalar_one_or_none()

            if not has_fund_this_month:
                # Get last active fund info
                last_fund_query = (
                    select(Budget.name, Budget.month, Budget.year)
                    .join(Fund, Budget.id == Fund.id)
                    .where(Fund.master_fund_id == master.id)
                    .order_by(Budget.year.desc(), Budget.month.desc())
                    .limit(1)
                )
                last_fund_result = await sess.execute(last_fund_query)
                last_fund = last_fund_result.first()

                orphaned_masters.append(
                    {
                        "master_id": master.id,
                        "name": master.name
                        or (last_fund.name if last_fund else "Unknown"),
                        "balance": float(master.total_amount),
                        "last_active_month": last_fund.month if last_fund else None,
                        "last_active_year": last_fund.year if last_fund else None,
                        "last_fund_name": last_fund.name if last_fund else None,
                    },
                )

        return orphaned_masters


async def discontinue_fund_master(
    master_fund_id: int,
    month: int,
    year: int,
    user_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Discontinue a fund master by withdrawing its balance.

    Creates a fund record for the specified month with negative month_amount
    equal to the master's balance, effectively returning the balance to the budget.

    Args:
        master_fund_id: Master fund ID to discontinue
        month: Month to record the discontinuation
        year: Year to record the discontinuation
        user_id: User ID
        session: Optional database session

    Returns:
        Dict with discontinuation info

    Raises:
        ValueError: If master not found or already has fund for this month

    """
    async with get_session(session) as sess:
        # Get master
        master_stmt = select(FundMaster).where(FundMaster.id == master_fund_id)
        master_result = await sess.execute(master_stmt)
        master = master_result.scalar_one_or_none()

        if not master:
            msg = f"Master fund {master_fund_id} not found"
            raise ValueError(msg)

        # Check if fund already exists for this month
        existing_fund_query = (
            select(Fund.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.master_fund_id == master_fund_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
            .limit(1)
        )
        existing_result = await sess.execute(existing_fund_query)
        existing_fund = existing_result.scalar_one_or_none()

        if existing_fund:
            msg = f"Fund already exists for master {master_fund_id} in {month}/{year}"
            raise ValueError(msg)

        # Get fund name from last active fund
        last_fund_query = (
            select(Budget.name)
            .join(Fund, Budget.id == Fund.id)
            .where(Fund.master_fund_id == master_fund_id)
            .order_by(Budget.year.desc(), Budget.month.desc())
            .limit(1)
        )
        last_fund_result = await sess.execute(last_fund_query)
        last_fund_name = last_fund_result.scalar_one_or_none() or "Discontinued Fund"

        # Create budget
        budget_id = await create_budget(
            user_id=user_id,
            name=last_fund_name,
            month=month,
            year=year,
            session=sess,
        )

        # Create fund with negative month_amount (withdrawal)
        withdrawal_amount = -master.total_amount
        fund_stmt = insert(Fund).values(
            id=budget_id,
            priority=999,  # Low priority for discontinued fund
            increment=Decimal("0.00"),
            month_amount=withdrawal_amount,
            max=None,
            master_fund_id=master_fund_id,
        )
        await sess.execute(fund_stmt)

        # Zero out master balance
        master.total_amount = Decimal("0.00")

        await sess.commit()

        return {
            "master_id": master_fund_id,
            "budget_id": budget_id,
            "withdrawal_amount": float(withdrawal_amount),
            "month": month,
            "year": year,
        }


async def add_fund_to_orphaned_master(
    master_fund_id: int,
    month: int,
    year: int,
    user_id: int,
    priority: int,
    increment: float,
    max_amount: float | None = None,
    session: AsyncSession | None = None,
) -> dict:
    """
    Add a fund to an orphaned master for the specified month.

    Args:
        master_fund_id: Orphaned master fund ID
        month: Month to add fund
        year: Year to add fund
        user_id: User ID
        priority: Fund priority
        increment: Monthly increment
        max_amount: Optional maximum fund amount
        session: Optional database session

    Returns:
        Dict with created fund info

    Raises:
        ValueError: If master not found or fund already exists for this month

    """
    async with get_session(session) as sess:
        # Get master
        master_stmt = select(FundMaster).where(FundMaster.id == master_fund_id)
        master_result = await sess.execute(master_stmt)
        master = master_result.scalar_one_or_none()

        if not master:
            msg = f"Master fund {master_fund_id} not found"
            raise ValueError(msg)

        # Check if fund already exists for this month
        existing_fund_query = (
            select(Fund.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.master_fund_id == master_fund_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
            .limit(1)
        )
        existing_result = await sess.execute(existing_fund_query)
        existing_fund = existing_result.scalar_one_or_none()

        if existing_fund:
            msg = f"Fund already exists for master {master_fund_id} in {month}/{year}"
            raise ValueError(msg)

        # Get last fund to get name (no longer tracking previous_fund_id)
        last_fund_query = (
            select(Budget.name)
            .join(Fund, Budget.id == Fund.id)
            .where(Fund.master_fund_id == master_fund_id)
            .order_by(Budget.year.desc(), Budget.month.desc())
            .limit(1)
        )
        last_fund_result = await sess.execute(last_fund_query)
        last_fund = last_fund_result.first()

        fund_name = master.name or (last_fund.name if last_fund else "Resumed Fund")

        # Create budget
        budget_id = await create_budget(
            user_id=user_id,
            name=fund_name,
            month=month,
            year=year,
            session=sess,
        )

        # Create fund
        fund_stmt = insert(Fund).values(
            id=budget_id,
            priority=priority,
            increment=Decimal(str(increment)),
            month_amount=Decimal("0.00"),
            max=Decimal(str(max_amount)) if max_amount is not None else None,
            master_fund_id=master_fund_id,
        )
        await sess.execute(fund_stmt)

        await sess.commit()

        return {
            "fund_id": budget_id,
            "master_id": master_fund_id,
            "master_balance": float(master.total_amount),
            "month": month,
            "year": year,
        }
