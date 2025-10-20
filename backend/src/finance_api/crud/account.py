from logging import getLogger
from sqlalchemy.dialects.postgresql import insert
from finance_api.models.account import SimpleFinAccount
from finance_api.schemas.schema import Account
from datetime import datetime, timezone
from finance_api.models.db import engine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
LOGGER = getLogger(__name__)


async def save_account(account: Account, user_id: int) -> None:
    """Save or update account using upsert.
    
    Args:
        account: Account object
    """
    import json
    
    stmt = insert(SimpleFinAccount).values(
        account_id=account.id,
        org_domain=account.org.domain,
        name=account.name,
        currency=account.currency,
        balance=account.balance,
        available_balance=account.available_balance,
        balance_date=account.balance_date,
        possible_error=account.possible_error,
        extra=account.extra,
        updated_at=datetime.now(timezone.utc),
        user_id=user_id
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=['account_id'],
        set_={
            'name': stmt.excluded.name,
            'currency': stmt.excluded.currency,
            'balance': stmt.excluded.balance,
            'available_balance': stmt.excluded.available_balance,
            'balance_date': stmt.excluded.balance_date,
            'possible_error': stmt.excluded.possible_error,
            'extra': stmt.excluded.extra,
            'updated_at': datetime.now(timezone.utc)
        }
    )
    async with AsyncSession(engine) as session:
        await session.execute(stmt)
        await session.commit()

    LOGGER.debug(f"Saved account: {account.name}")


async def get_user_accounts(user_id: int) -> list[SimpleFinAccount]:
    """Get all accounts for a user."""


    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(SimpleFinAccount).where(SimpleFinAccount.user_id == user_id)
        )
        return list(result.scalars().all())