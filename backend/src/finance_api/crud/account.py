"""Account CRUD operations."""

from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.account import SimpleFinAccount
from finance_api.models.db import get_session
from finance_api.schemas.schema import Account

LOGGER = getLogger(__name__)


async def save_account(
    account: Account,
    user_id: int,
    session: AsyncSession | None = None,
) -> None:
    """
    Save or update account using upsert.

    Args:
        account: Account object to save
        user_id: ID of the user who owns the account
        session: Optional database session. If None, creates a new session.

    """
    async with get_session(session) as sess:
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
            updated_at=datetime.now(UTC),
            user_id=user_id,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["account_id"],
            set_={
                "name": stmt.excluded.name,
                "currency": stmt.excluded.currency,
                "balance": stmt.excluded.balance,
                "available_balance": stmt.excluded.available_balance,
                "balance_date": stmt.excluded.balance_date,
                "possible_error": stmt.excluded.possible_error,
                "extra": stmt.excluded.extra,
                "updated_at": datetime.now(UTC),
            },
        )
        await sess.execute(stmt)
        await sess.commit()
        LOGGER.debug("Saved account: %s", account.name)


async def get_user_accounts(
    user_id: int,
    session: AsyncSession | None = None,
) -> list[SimpleFinAccount]:
    """Get all accounts for a user."""
    async with get_session(session) as sess:
        result = await sess.execute(
            select(SimpleFinAccount).where(SimpleFinAccount.user_id == user_id),
        )
        return list(result.scalars().all())
