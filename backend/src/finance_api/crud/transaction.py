from finance_api.models.account import SimpleFinAccount
from sqlalchemy import asc, desc, func, insert, select, update
from finance_api.schemas.schema import Transaction
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from logging import getLogger
from finance_api.models.db import engine
from sqlalchemy.ext.asyncio import AsyncSession
from finance_api.models.transaction import SimpleFinTransaction, TransactionLineItem
from finance_api.models.user import User
from sqlalchemy.orm import selectinload
LOGGER = getLogger(__name__)


async def save_transactions(
    account_id: str, transactions: List[Transaction]
) -> None:
    """Save or update transactions using upsert.

    Args:
        account_id: Account ID
        transaction_list: List of Transaction objects
    """
    if not transactions:
        return

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
            updated_at=datetime.now(timezone.utc),
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
                "updated_at": datetime.now(timezone.utc),
            },
        )
        async with AsyncSession(engine) as session:
             await session.execute(stmt)
             await session.commit()

    LOGGER.debug(f"Saved {len(transactions)} transactions for account {account_id}")

async def get_transactions(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_excluded: bool = False,
    transaction_types: Optional[list[str]] = None,
    sort_desc: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> list[SimpleFinTransaction]:
    """
    Get transactions with filtering options.
    
    Args:
        user_id: User ID
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date
        include_excluded: If False (default), exclude transactions marked as exclude_from_budget
        transaction_types: Filter by specific transaction types. If None, shows all types
        sort_desc: Sort by date descending
        limit: Max results
        offset: Pagination offset
    """
    async with AsyncSession(engine) as session:
        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
            .options(selectinload(SimpleFinTransaction.budget))
            .options(selectinload(SimpleFinTransaction.account).selectinload(SimpleFinAccount.org))
        )
        
        # Filter out excluded transactions by default
        if not include_excluded:
            stmt = stmt.where(SimpleFinTransaction.exclude_from_budget == False)
        
        # Filter by transaction types if specified
        if transaction_types is not None:
            stmt = stmt.where(SimpleFinTransaction.transaction_type.in_(transaction_types))
        
        if start_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at >= start_date)
        if end_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at <= end_date)
        
        if sort_desc:
            stmt = stmt.order_by(desc(SimpleFinTransaction.transacted_at))
        else:
            stmt = stmt.order_by(asc(SimpleFinTransaction.transacted_at))
        
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

async def assign_transaction_to_budget(
    transaction_id: int, budget_id: int
) -> None:
    """Assign a transaction to a budget."""
    async with AsyncSession(engine) as session:
        await session.execute(
            update(SimpleFinTransaction)
            .where(SimpleFinTransaction.id == transaction_id)
            .values(budget_id=budget_id)
        )
        await session.commit()

async def create_transaction_breakdown(
    transaction_id: int,
    line_items: list[dict],
) -> list[TransactionLineItem]:
    """
    Break down a transaction into line items.
    
    Args:
        transaction_id: The parent transaction ID
        line_items: List of dicts with keys: description, amount, quantity, unit_price, category, budget_id, notes
    
    Example:
        line_items = [
            {"description": "Bananas", "amount": 3.50, "quantity": 2, "unit_price": 1.75, "budget_id": 5},
            {"description": "Water", "amount": 2.00, "quantity": 1, "unit_price": 2.00, "budget_id": 5},
            {"description": "Sales Tax", "amount": 0.44, "category": "tax", "budget_id": 5},
        ]
    """
    async with AsyncSession(engine) as session:
        # Get parent transaction
        transaction = await session.get(SimpleFinTransaction, transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Validate total matches parent transaction
        line_items_total = sum(item["amount"] for item in line_items)
        if abs(line_items_total - transaction.amount) > 0.01:  # Allow 1 cent rounding
            raise ValueError(
                f"Line items total ({line_items_total}) doesn't match transaction amount ({transaction.amount})"
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
            session.add(line_item)
            created_items.append(line_item)
        
        # Mark parent as split
        transaction.is_split = True
        
        await session.commit()
        return created_items

async def get_transaction_with_breakdown(transaction_id: int) -> Optional[dict]:
    """Get a transaction with all its line items."""
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(SimpleFinTransaction)
            .where(SimpleFinTransaction.id == transaction_id)
            .options(selectinload(SimpleFinTransaction.line_items))
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
            ] if transaction.is_split else []
        }

async def update_line_item(
    line_item_id: int,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    quantity: Optional[float] = None,
    unit_price: Optional[float] = None,
    category: Optional[str] = None,
    budget_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> TransactionLineItem:
    """Update a line item."""
    async with AsyncSession(engine) as session:
        line_item = await session.get(TransactionLineItem, line_item_id)
        if not line_item:
            raise ValueError(f"Line item {line_item_id} not found")
        
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
        
        await session.commit()
        return line_item

async def delete_line_item(line_item_id: int) -> None:
    """Delete a line item."""
    async with AsyncSession(engine) as session:
        line_item = await session.get(TransactionLineItem, line_item_id)
        if not line_item:
            raise ValueError(f"Line item {line_item_id} not found")
        
        await session.delete(line_item)
        await session.commit()

async def mark_transaction_type(
    transaction_id: int,
    transaction_type: Optional[str] = None,
    exclude_from_budget: bool = False,
) -> SimpleFinTransaction:
    """
    Mark a transaction with a specific type and/or exclude it from budgets.
    
    Args:
        transaction_id: The transaction ID
        transaction_type: One of: 'transfer', 'credit_payment', 'loan_payment', or None
        exclude_from_budget: If True, exclude from all budget calculations
    
    Valid transaction types:
        - 'transfer': Money moving between your own accounts
        - 'credit_payment': Paying off a credit card
        - 'loan_payment': Paying off a loan
        - None: Regular transaction (default)
    """
    valid_types = ['transfer', 'credit_payment', 'loan_payment', None]
    if transaction_type not in valid_types:
        raise ValueError(f"Invalid transaction type. Must be one of: {valid_types}")
    
    async with AsyncSession(engine) as session:
        transaction = await session.get(SimpleFinTransaction, transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        transaction.transaction_type = transaction_type
        transaction.exclude_from_budget = exclude_from_budget
        
        await session.commit()
        await session.refresh(transaction)
        return transaction




# Currently not used, but may be useful for future reporting features
async def get_excluded_transactions(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SimpleFinTransaction]:
    """Get only excluded transactions (transfers, payments, etc)."""
    async with AsyncSession(engine) as session:
        stmt = (
            select(SimpleFinTransaction)
            .join(SimpleFinAccount)
            .where(SimpleFinAccount.user_id == user_id)
            .where(SimpleFinTransaction.exclude_from_budget == True)
            .options(selectinload(SimpleFinTransaction.account))
        )
        
        if start_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at >= start_date)
        if end_date:
            stmt = stmt.where(SimpleFinTransaction.transacted_at <= end_date)
        
        stmt = stmt.order_by(desc(SimpleFinTransaction.transacted_at))
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())