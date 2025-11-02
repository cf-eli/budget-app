"""Income budget CRUD operations."""

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Income
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction

from .base import create_budget


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
