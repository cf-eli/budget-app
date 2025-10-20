
from sqlalchemy.ext.declarative import declarative_base
from finance_api.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_HOST = settings.db_host
DB_NAME = settings.finance_db_name
DB_PORT = settings.db_port
DB_USER = settings.db_user
DB_PASSWORD = settings.db_password

Base = declarative_base()

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # logs all SQL
    pool_pre_ping=True,  # Verify connections before using
)

async def test_connection() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT NOW()"))
        print(result.fetchone())

