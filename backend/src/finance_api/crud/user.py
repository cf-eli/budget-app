"""User CRUD operations."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.models.account import SimpleFinAccount
from finance_api.models.db import get_session
from finance_api.models.user import User


async def get_user(
    auth_user_id: str,
    include_user_data: bool = False,
    session: AsyncSession | None = None,
) -> User | None:
    """Get user by auth_user_id with optional related data."""
    async with get_session(session) as sess:
        stmt = select(User).where(User.auth_user_id == auth_user_id)
        if include_user_data:
            stmt = stmt.options(
                selectinload(User.accounts).selectinload(SimpleFinAccount.transactions),
                selectinload(User.budgets),
            )
        result = await sess.execute(stmt)
        return result.scalars().one_or_none()


async def create_user(auth_user_id: str, session: AsyncSession | None = None) -> None:
    """Create a new user."""
    async with get_session(session) as sess:
        user = User(auth_user_id=auth_user_id)
        sess.add(user)
        await sess.commit()


async def ensure_user(auth_user_id: str, session: AsyncSession | None = None) -> User:
    """Ensure a user exists, creating them if necessary."""
    user = await get_user(auth_user_id, session=session)
    if user is None:
        await create_user(auth_user_id, session=session)
        user = await get_user(auth_user_id, session=session)
    return user


async def get_all_users(session: AsyncSession | None = None) -> list[User]:
    """List all users."""
    async with get_session(session) as sess:
        result = await sess.execute(select(User))
        return list(result.scalars().all())


async def update_access_url(
    auth_user_id: str,
    access_url: str,
    session: AsyncSession | None = None,
) -> None:
    """Update the access URL for a user."""
    async with get_session(session) as sess:
        await sess.execute(
            update(User)
            .values(access_url=access_url)
            .where(User.auth_user_id == auth_user_id),
        )
        await sess.commit()
