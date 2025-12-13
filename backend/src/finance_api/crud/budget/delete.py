"""Budget deletion operations."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget
from finance_api.models.db import get_session


async def delete_budget_by_id(
    budget_id: int,
    user_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Delete a specific budget by ID.

    This function deletes a single budget entry by its ID after verifying
    it belongs to the specified user. The deletion cascades to related
    entries due to database constraints.

    Args:
        budget_id: The budget ID to delete
        user_id: The user ID (for verification)
        session: Optional database session

    Returns:
        Dict with success key indicating deletion status

    Raises:
        ValueError: If budget not found or doesn't belong to user

    """
    async with get_session(session) as sess:
        # First check if budget exists and belongs to user
        query = (
            select(Budget)
            .where(Budget.id == budget_id)
            .where(Budget.user_id == user_id)
        )
        result = await sess.execute(query)
        budget = result.scalar_one_or_none()

        if not budget:
            msg = f"Budget {budget_id} not found or doesn't belong to user"
            raise ValueError(msg)

        # Delete the budget
        delete_query = (
            delete(Budget)
            .where(Budget.id == budget_id)
            .where(Budget.user_id == user_id)
        )
        await sess.execute(delete_query)
        await sess.commit()

        return {"success": True}


async def delete_budgets(
    user_id: int,
    month: int,
    year: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Delete all budgets for a specific month and year.

    This function deletes all budget entries (income, expenses, funds)
    for the specified user, month, and year. The deletion cascades to
    related entries due to database constraints.

    Args:
        user_id: The user ID
        month: Month to delete budgets for (1-12)
        year: Year to delete budgets for (e.g., 2024)
        session: Optional database session

    Returns:
        Dict with deleted_count key indicating number of budgets deleted

    Raises:
        ValueError: If no budgets found for the specified month/year

    """
    async with get_session(session) as sess:
        # First check if any budgets exist
        count_query = (
            select(Budget)
            .where(Budget.user_id == user_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
        )
        result = await sess.execute(count_query)
        budgets = result.scalars().all()

        if not budgets:
            msg = f"No budgets found for month {month}, year {year}"
            raise ValueError(msg)

        deleted_count = len(budgets)

        # Delete all budgets for the month/year
        delete_query = (
            delete(Budget)
            .where(Budget.user_id == user_id)
            .where(Budget.month == month)
            .where(Budget.year == year)
        )
        await sess.execute(delete_query)
        await sess.commit()

        return {"deleted_count": deleted_count}
