"""Basic transaction operations."""

from datetime import UTC, datetime
from logging import getLogger

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction
from finance_api.schemas.schema import Transaction

LOGGER = getLogger(__name__)


async def save_transactions(
    account_id: str,
    transactions: list[Transaction],
    session: AsyncSession | None = None,
) -> None:
    """
    Save or update transactions using upsert.

    Args:
        account_id: Account ID to associate transactions with
        transactions: List of Transaction objects to save
        session: Optional database session. If None, creates a new session.

    """
    if not transactions:
        return

    async with get_session(session) as sess:
        for transaction in transactions:
            stmt = insert(SimpleFinTransaction).values(
                transaction_id=transaction.id,
                account_id=account_id,
                posted=transaction.posted,
                amount=transaction.amount,
                description=transaction.description,
                payee=transaction.payee,
                memo=transaction.memo,
                transacted_at=transaction.transacted_at,
                pending=transaction.pending,
                updated_at=datetime.now(UTC),
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=["transaction_id"],
                set_={
                    "posted": stmt.excluded.posted,
                    "amount": stmt.excluded.amount,
                    "description": stmt.excluded.description,
                    "payee": stmt.excluded.payee,
                    "memo": stmt.excluded.memo,
                    "transacted_at": stmt.excluded.transacted_at,
                    "pending": stmt.excluded.pending,
                    "updated_at": datetime.now(UTC),
                },
            )
            await sess.execute(stmt)
            await sess.commit()
        LOGGER.debug(
            "Saved %d transactions for account %s",
            len(transactions),
            account_id,
        )


async def mark_transaction_type(
    transaction_id: int,
    transaction_type: str | None = None,
    exclude_from_budget: bool = False,
    session: AsyncSession | None = None,
) -> SimpleFinTransaction:
    """
    Mark a transaction with a specific type and/or exclude it from budgets.

    Args:
        transaction_id: The transaction ID
        transaction_type: One of: 'transfer', 'credit_payment', 'loan_payment', or None
        exclude_from_budget: If True, exclude from all budget calculations
        session: Optional database session. If None, creates a new session.

    Valid transaction types:
        - 'transfer': Money moving between your own accounts
        - 'credit_payment': Paying off a credit card
        - 'loan_payment': Paying off a loan
        - None: Regular transaction (default)

    """
    valid_types = ["transfer", "credit_payment", "loan_payment", None]
    if transaction_type not in valid_types:
        msg = f"Invalid transaction type. Must be one of: {valid_types}"
        raise ValueError(msg)

    async with get_session(session) as sess:
        transaction = await sess.get(SimpleFinTransaction, transaction_id)
        if not transaction:
            msg = f"Transaction {transaction_id} not found"
            raise ValueError(msg)

        transaction.transaction_type = transaction_type
        transaction.exclude_from_budget = exclude_from_budget

        await sess.commit()
        await sess.refresh(transaction)
        return transaction


# Currently not used, but may be useful for future reporting features
