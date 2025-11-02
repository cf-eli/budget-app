"""Transaction query operations."""

from calendar import monthrange
from datetime import UTC, datetime

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.models.account import SimpleFinAccount
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction


async def get_transactions(
    user_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    include_excluded: bool = False,
    transaction_types: list[str] | None = None,
    sort_desc: bool = True,
    limit: int = 100,
    offset: int = 0,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> list[SimpleFinTransaction]:
    """
    Get transactions with filtering options.

    Args:
        user_id: User ID
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date
        include_excluded: If False (default), exclude transactions
          marked as exclude_from_budget
        transaction_types: Filter by specific transaction types.
          If None, shows all types
        sort_desc: Sort by date descending
        limit: Max results
        offset: Pagination offset
        month: Filter by month (1-12). If provided with year,
          filters transactions to that month/year. Defaults to current month
        year: Filter by year (e.g., 2024). If provided with month,
          filters transactions to that month/year. Defaults to current year
        session: Optional database session. If None, creates a new session.

    """
    async with get_session(session) as sess:
        # Use current month/year if not provided
        now = datetime.now(UTC)
        if month is None:
            month = now.month
        if year is None:
            year = now.year

        # Calculate start and end dates for the month/year
        month_start = datetime(year, month, 1, tzinfo=UTC)
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
            .options(selectinload(SimpleFinTransaction.budget))
            .options(
                selectinload(SimpleFinTransaction.account).selectinload(
                    SimpleFinAccount.org,
                ),
            )
        )

        # Filter out excluded transactions by default
        if not include_excluded:
            stmt = stmt.where(~SimpleFinTransaction.exclude_from_budget)

        # Filter by transaction types if specified
        if transaction_types is not None:
            stmt = stmt.where(
                SimpleFinTransaction.transaction_type.in_(transaction_types),
            )

        # Apply month/year filtering
        stmt = stmt.where(SimpleFinTransaction.transacted_at >= month_start)
        stmt = stmt.where(SimpleFinTransaction.transacted_at <= month_end)

        # Additional date filtering if specified
        if start_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at >= start_date)
        if end_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at <= end_date)

        if sort_desc:
            stmt = stmt.order_by(desc(SimpleFinTransaction.transacted_at))
        else:
            stmt = stmt.order_by(asc(SimpleFinTransaction.transacted_at))

        stmt = stmt.limit(limit).offset(offset)
        result = await sess.execute(stmt)
        return list(result.scalars().all())


async def get_transactions_paginated(
    user_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    include_excluded: bool = False,
    transaction_types: list[str] | None = None,
    sort_desc: bool = True,
    limit: int = 100,
    offset: int = 0,
    month: int | None = None,
    year: int | None = None,
    session: AsyncSession | None = None,
) -> tuple[list[SimpleFinTransaction], int]:
    """
    Get transactions with filtering options and total count.

    Args:
        user_id: User ID
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date
        include_excluded: If False (default), exclude transactions
          marked as exclude_from_budget
        transaction_types: Filter by specific transaction types.
          If None, shows all types
        sort_desc: Sort by date descending
        limit: Max results
        offset: Pagination offset
        month: Filter by month (1-12). If provided with year,
          filters transactions to that month/year. Defaults to current month
        year: Filter by year (e.g., 2024). If provided with month,
          filters transactions to that month/year. Defaults to current year
        session: Optional database session. If None, creates a new session.

    Returns:
        Tuple of (transactions list, total count)

    """
    async with get_session(session) as sess:
        # Use current month/year if not provided
        now = datetime.now(UTC)
        if month is None:
            month = now.month
        if year is None:
            year = now.year

        # Calculate start and end dates for the month/year
        month_start = datetime(year, month, 1, tzinfo=UTC)
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        # Build base query for filtering
        base_stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
        )

        # Filter out excluded transactions by default
        if not include_excluded:
            base_stmt = base_stmt.where(~SimpleFinTransaction.exclude_from_budget)

        # Filter by transaction types if specified
        if transaction_types is not None:
            base_stmt = base_stmt.where(
                SimpleFinTransaction.transaction_type.in_(transaction_types),
            )

        # Apply month/year filtering
        base_stmt = base_stmt.where(SimpleFinTransaction.transacted_at >= month_start)
        base_stmt = base_stmt.where(SimpleFinTransaction.transacted_at <= month_end)

        # Additional date filtering if specified
        if start_date:
            base_stmt = base_stmt.where(
                SimpleFinTransaction.transacted_at >= start_date,
            )
        if end_date:
            base_stmt = base_stmt.where(
                SimpleFinTransaction.transacted_at <= end_date,
            )

        # Get total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await sess.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        stmt = base_stmt.options(selectinload(SimpleFinTransaction.budget)).options(
            selectinload(SimpleFinTransaction.account).selectinload(
                SimpleFinAccount.org,
            ),
        )

        if sort_desc:
            stmt = stmt.order_by(desc(SimpleFinTransaction.transacted_at))
        else:
            stmt = stmt.order_by(asc(SimpleFinTransaction.transacted_at))

        stmt = stmt.limit(limit).offset(offset)
        result = await sess.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total


async def get_excluded_transactions(
    user_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession | None = None,
) -> list[SimpleFinTransaction]:
    """Get only excluded transactions (transfers, payments, etc)."""
    async with get_session(session) as sess:
        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
            .where(SimpleFinTransaction.exclude_from_budget)
            .options(selectinload(SimpleFinTransaction.account))
        )

        if start_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at >= start_date)
        if end_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at <= end_date)

        stmt = stmt.order_by(desc(SimpleFinTransaction.transacted_at))
        stmt = stmt.limit(limit).offset(offset)
        result = await sess.execute(stmt)
        return list(result.scalars().all())
