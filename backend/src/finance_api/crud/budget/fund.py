"""Fund budget CRUD operations."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund, FundMaster
from finance_api.models.db import get_session

from .base import create_budget


async def create_fund(
    user_id: int,
    name: str,
    priority: int | None,
    increment: float | None,
    month_amount: float = 0.0,
    max_amount: float | None = None,
    month: int | None = None,
    year: int | None = None,
    master_fund_id: int | None = None,
    session: AsyncSession | None = None,
) -> int:
    """
    Create a budget with fund details.

    Args:
        user_id: User ID
        name: Fund name
        priority: Fund priority for allocation
        increment: Monthly increment amount
        month_amount: Initial month amount (default 0.0)
        max_amount: Optional maximum fund amount
        month: Month (default current month)
        year: Year (default current year)
        master_fund_id: Optional existing master fund ID to link to
        session: Optional database session

    Returns:
        The created budget ID

    """
    budget_id = await create_budget(
        user_id,
        name,
        month=month,
        year=year,
        session=session,
    )

    async with get_session(session) as sess:
        # Create or use existing master fund
        if master_fund_id is None:
            # Create new master fund
            master = FundMaster(
                name=name,
                total_amount=Decimal("0.00"),
                created_at=datetime.now(UTC),
            )
            sess.add(master)
            await sess.flush()  # Get the ID
            master_fund_id = master.id

        # Create fund linked to master
        stmt = insert(Fund).values(
            id=budget_id,
            priority=priority,
            increment=Decimal(str(increment))
            if increment is not None
            else Decimal("0.00"),
            month_amount=Decimal(str(month_amount)),
            max=Decimal(str(max_amount)) if max_amount is not None else None,
            master_fund_id=master_fund_id,
        )
        await sess.execute(stmt)
        await sess.commit()

    return budget_id


async def get_fund_sum(user_id: int, session: AsyncSession | None = None) -> float:
    """
    Get total monthly fund contributions for a user.

    This sums the month_amount (monthly contribution) for funds, not the master
    balance which is cumulative. This is used in budget summary calculations.
    """
    query = (
        select(func.sum(Fund.month_amount))
        .select_from(Budget)
        .join(Fund, Budget.id == Fund.id)
        .where(Budget.user_id == user_id)
    )

    async with get_session(session) as sess:
        result = await sess.execute(query)
        return float(result.scalar() or 0.0)
