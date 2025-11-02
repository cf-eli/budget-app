"""Database configuration and engine setup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base

from finance_api.config import settings

DB_HOST = settings.db_host
DB_NAME = settings.finance_db_name
DB_PORT = settings.db_port
DB_USER = settings.db_user
DB_PASSWORD = settings.db_password

Base = declarative_base()

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
)


@asynccontextmanager
async def get_session(
    session: AsyncSession | None = None,
) -> AsyncIterator[AsyncSession]:
    """
    Get existing session or create a new one.

    Args:
        session: Optional existing session to use. If None, creates a new one.

    Yields:
        AsyncSession: The session to use for database operations.

    """
    if session is not None:
        yield session
    else:
        async with AsyncSession(engine) as new_session:
            yield new_session


async def test_connection() -> None:  # pragma: no cover
    """Test database connection."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT NOW()"))
        # Connection test successful
        _ = result.fetchone()
