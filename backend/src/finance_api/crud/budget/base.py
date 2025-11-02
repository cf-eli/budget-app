"""Base budget CRUD operations."""

from datetime import UTC, datetime

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget
from finance_api.models.db import get_session


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
