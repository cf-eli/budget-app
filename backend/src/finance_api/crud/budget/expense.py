"""Expense budget CRUD operations."""

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Expense
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction

from .base import create_budget


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
