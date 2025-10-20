# import sqlalchemy core
from sqlalchemy import select, update
from finance_api.models.user import User
from finance_api.models.db import engine
from sqlalchemy.dialects.postgresql import insert as insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from finance_api.models.account import SimpleFinAccount

# async def get_user(user: str) -> User | None:
#     """Get user by auth_user_id."""

async def get_user(auth_user_id: str, include_user_data: bool = False) -> User | None:
    async with AsyncSession(engine) as session:
        stmt = select(User).where(User.auth_user_id == auth_user_id)
        if include_user_data:
            stmt = stmt.options(
                selectinload(User.accounts).selectinload(SimpleFinAccount.transactions),
                selectinload(User.budgets),
            )
        result = await session.execute(stmt)
        return result.scalars().one_or_none()


async def create_user(auth_user_id: str) -> None:
    """Create a new user."""
    async with AsyncSession(engine) as session:
        user = User(auth_user_id=auth_user_id)
        session.add(user)
        await session.commit()


async def ensure_user(auth_user_id: str) -> User:
    """Ensure a user exists, creating them if necessary."""
    user = await get_user(auth_user_id)
    if user is None:
        await create_user(auth_user_id)
        user = await get_user(auth_user_id)
    print("Ensured user:", user)
    return user


async def get_all_users() -> list[User]:
    """List all users."""
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User))
        return list(result.scalars().all())


async def update_access_url(auth_user_id: str, access_url: str) -> None:
    """Update the access URL for a user."""
    async with AsyncSession(engine) as session:
        await session.execute(
            update(User)
            .values(access_url=access_url)
            .where(User.auth_user_id == auth_user_id)
        )
        await session.commit()


# def create_user(auth_user_id: str, user_name: str):
#     query = insert(User).values(auth_user_id=auth_user_id, user_name=user_name)
#     return database.execute_query(query=query)


# def create_user_items(auth_user_id: str, item_id: str):
#     query = insert(UserItems).values(auth_user_id=auth_user_id, item_id=item_id)
#     return database.execute_query(query=query)


# def get_user(auth_user_id: str):
#     query = select(User).where(User.auth_user_id == auth_user_id)
#     return database.execute_query(query=query, fetch_all=False)


# def get_user_items(auth_user_id: str):
#     query = (
#         select(Item)
#         .join(UserItems)
#         .where(UserItems.auth_user_id == auth_user_id)
#         .execution_options(populate_existing=True)
#     )
#     results = database.execute_query(query=query)
#     return [Item(**dict(row._mapping)) for row in results]


# def create_user_account(auth_user_id: str, account_id: str):
#     query = insert(UserAccount).values(auth_user_id=auth_user_id, account_id=account_id)
#     return database.execute_query(query=query)
