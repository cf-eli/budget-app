"""Transaction breakdown operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction, TransactionLineItem

from .assignment import _update_fund_amount_for_transaction

# Transaction line item validation tolerance (1 cent for rounding)
LINE_ITEM_AMOUNT_TOLERANCE = 0.01


async def create_transaction_breakdown(
    transaction_id: int,
    line_items: list[dict],
    session: AsyncSession | None = None,
) -> list[TransactionLineItem]:
    """
    Break down a transaction into line items.

    Args:
        transaction_id: The parent transaction ID
        line_items: List of dicts with keys: description, amount,
          quantity, unit_price, category, budget_id, notes
        session: Optional database session. If None, creates a new session.

    Example:
        line_items = [
            {"description": "Bananas", "amount": 3.50, "quantity": 2,
              "unit_price": 1.75, "budget_id": 5},
            {"description": "Water", "amount": 2.00, "quantity": 1,
              "unit_price": 2.00, "budget_id": 5},
            {"description": "Sales Tax", "amount": 0.44, "category": "tax",
              "budget_id": 5},
        ]

    """
    async with get_session(session) as sess:
        # Get parent transaction
        transaction = await sess.get(SimpleFinTransaction, transaction_id)
        if not transaction:
            msg = f"Transaction {transaction_id} not found"
            raise ValueError(msg)

        # Validate total matches parent transaction
        line_items_total = sum(item["amount"] for item in line_items)
        if abs(line_items_total - transaction.amount) > LINE_ITEM_AMOUNT_TOLERANCE:
            msg = (
                f"Line items total ({line_items_total}) doesn't match transaction "
                f"amount ({transaction.amount})"
            )
            raise ValueError(
                msg,
            )

        # Create line items
        created_items = []
        for item_data in line_items:
            line_item = TransactionLineItem(
                parent_transaction_id=transaction_id,
                description=item_data["description"],
                amount=item_data["amount"],
                quantity=item_data.get("quantity"),
                unit_price=item_data.get("unit_price"),
                category=item_data.get("category"),
                budget_id=item_data.get("budget_id"),
                notes=item_data.get("notes"),
            )
            sess.add(line_item)
            created_items.append(line_item)

        # Mark parent as split
        transaction.is_split = True

        await sess.commit()
        return created_items


async def get_transaction_with_breakdown(
    transaction_id: int,
    session: AsyncSession | None = None,
) -> dict | None:
    """Get a transaction with all its line items."""
    async with get_session(session) as sess:
        result = await sess.execute(
            select(SimpleFinTransaction)
            .where(SimpleFinTransaction.id == transaction_id)
            .options(selectinload(SimpleFinTransaction.line_items)),
        )
        transaction = result.scalars().one_or_none()

        if not transaction:
            return None

        return {
            "id": transaction.id,
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "description": transaction.description,
            "payee": transaction.payee,
            "transacted_at": transaction.transacted_at,
            "is_split": transaction.is_split,
            "budget_id": transaction.budget_id,
            "line_items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "amount": item.amount,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "category": item.category,
                    "budget_id": item.budget_id,
                    "notes": item.notes,
                }
                for item in transaction.line_items
            ]
            if transaction.is_split
            else [],
        }


async def update_line_item(  # noqa: C901
    line_item_id: int,
    description: str | None = None,
    amount: float | None = None,
    quantity: float | None = None,
    unit_price: float | None = None,
    category: str | None = None,
    budget_id: int | None = None,
    notes: str | None = None,
    session: AsyncSession | None = None,
) -> TransactionLineItem:
    """
    Update a line item.

    If budget_id is changed and involves a fund, this will update the fund amounts.
    """
    async with get_session(session) as sess:
        line_item = await sess.get(TransactionLineItem, line_item_id)
        if not line_item:
            msg = f"Line item {line_item_id} not found"
            raise ValueError(msg)

        old_budget_id = line_item.budget_id
        old_amount = line_item.amount

        if description is not None:
            line_item.description = description
        if amount is not None:
            line_item.amount = amount
        if quantity is not None:
            line_item.quantity = quantity
        if unit_price is not None:
            line_item.unit_price = unit_price
        if category is not None:
            line_item.category = category
        if budget_id is not None:
            line_item.budget_id = budget_id
        if notes is not None:
            line_item.notes = notes

        # Handle fund amount updates when budget assignment or amount changes
        new_amount = line_item.amount
        new_budget_id = line_item.budget_id

        # If budget changed, update both old and new funds
        if budget_id is not None and old_budget_id != new_budget_id:
            # Restore amount to old fund
            if old_budget_id:
                await _update_fund_amount_for_transaction(
                    old_budget_id,
                    -old_amount,  # Restore
                    sess,
                )
            # Reduce amount from new fund
            if new_budget_id:
                await _update_fund_amount_for_transaction(
                    new_budget_id,
                    new_amount,  # Reduce
                    sess,
                )
        # If only amount changed but budget stayed the same, update the fund
        elif amount is not None and old_amount != new_amount and new_budget_id:
            amount_delta = new_amount - old_amount
            await _update_fund_amount_for_transaction(
                new_budget_id,
                amount_delta,
                sess,
            )

        await sess.commit()
        return line_item


async def delete_line_item(
    line_item_id: int,
    session: AsyncSession | None = None,
) -> None:
    """Delete a line item."""
    async with get_session(session) as sess:
        line_item = await sess.get(TransactionLineItem, line_item_id)
        if not line_item:
            msg = f"Line item {line_item_id} not found"
            raise ValueError(msg)

        await sess.delete(line_item)
        await sess.commit()
