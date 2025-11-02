"""Transaction budget assignment operations."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction


async def assign_transaction_to_budget(
    transaction_id: int,
    budget_id: int,
    session: AsyncSession | None = None,
) -> None:
    """
    Assign a transaction to a budget.

    For funds with the master fund system:
    - Transactions tracked separately via get_budget_sum_with_line_items()
    - month_amount is NOT modified (it represents allocation only)
    - Master balance = sum(month_amount + transaction_sum) for all funds

    For regular budgets (income/expense/flexible):
    - Transaction is simply linked to the budget
    """
    async with get_session(session) as sess:
        # Get the transaction to check its amount and old budget
        transaction_query = select(SimpleFinTransaction).where(
            SimpleFinTransaction.id == transaction_id,
        )
        transaction_result = await sess.execute(transaction_query)
        transaction = transaction_result.scalar_one_or_none()

        if not transaction:
            msg = f"Transaction {transaction_id} not found"
            raise ValueError(msg)

        old_budget_id = transaction.budget_id
        transaction_amount = transaction.amount

        # Update the transaction's budget assignment
        await sess.execute(
            update(SimpleFinTransaction)
            .where(SimpleFinTransaction.id == transaction_id)
            .values(budget_id=budget_id),
        )

        # If removing from an old fund, restore its amount
        if old_budget_id:
            await _update_fund_amount_for_transaction(
                old_budget_id,
                -transaction_amount,  # Restore (opposite of spending)
                sess,
            )

        # If assigning to a new fund, reduce its amount
        if budget_id:
            await _update_fund_amount_for_transaction(
                budget_id,
                transaction_amount,  # Reduce by spending
                sess,
            )

        await sess.commit()


async def _update_fund_amount_for_transaction(
    budget_id: int,
    transaction_amount: float,  # noqa: ARG001
    session: AsyncSession,
) -> None:
    """
    Update fund amount when a transaction is assigned/unassigned.

    With the master fund system and dynamic balance calculation, we NO LONGER
    modify month_amount when transactions are assigned. The month_amount
    represents the allocation TO the fund, and transactions tracked separately.

    Master balance = sum(month_amount + transaction_sum) for all funds.

    This function is now a no-op for funds but kept for backwards compatibility.

    Args:
        budget_id: The budget/fund ID
        transaction_amount: Transaction amount (negative for expenses,
            positive for income)
        session: Database session

    """
    # Check if this budget is a fund
    fund_query = (
        select(Fund, Budget)
        .join(Budget, Fund.id == Budget.id)
        .where(Fund.id == budget_id)
    )
    fund_result = await session.execute(fund_query)
    fund_data = fund_result.first()

    if not fund_data:
        # Not a fund, nothing to do
        return

    # For funds: Do nothing. Transactions are tracked separately via
    # get_budget_sum_with_line_items() and master balance is calculated dynamically.
    # Modifying month_amount would cause double-counting.
    return
