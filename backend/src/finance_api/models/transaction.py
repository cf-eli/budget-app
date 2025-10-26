"""SimpleFin transaction model for financial transactions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finance_api.models.db import Base

if TYPE_CHECKING:
    from finance_api.models.account import (
        SimpleFinAccount,
    )
    from finance_api.models.budget import Budget


class SimpleFinTransaction(Base):
    """SimpleFin transaction model representing a financial transaction."""

    __tablename__ = "simplefin_transaction"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        server_default=None,
        nullable=False,
    )

    posted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.0",
        default=0.0,
    )
    description: Mapped[str | None] = mapped_column(
        String,
        nullable=False,
        server_default="",
        default="",
    )
    payee: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        server_default=None,
        default=None,
    )
    memo: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        server_default=None,
        default=None,
    )
    transacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    pending: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
        default=False,
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        server_default=None,
        default=None,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # If this transaction has been split into line items
    is_split: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
    )
    # Transaction type for filtering
    transaction_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
    )  # Values: 'transfer', 'credit_payment', 'loan_payment', None
    exclude_from_budget: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
    )  # If True, exclude from budget calculations

    budget_id: Mapped[int | None] = mapped_column(
        ForeignKey("budget.id"),
        nullable=True,
    )
    account_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("simplefin_account.account_id"),
        nullable=False,
    )

    account: Mapped["SimpleFinAccount"] = relationship(back_populates="transactions")
    budget: Mapped[Optional["Budget"]] = relationship(back_populates="transactions")

    line_items: Mapped[list["TransactionLineItem"]] = relationship(
        back_populates="parent_transaction",
        cascade="all, delete-orphan",
    )


class TransactionLineItem(Base):
    """Individual items within a transaction (e.g., products in a store receipt)."""

    __tablename__ = "transaction_line_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("simplefin_transaction.id"),
        nullable=False,
        index=True,
    )

    # Line item details
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True, default=1.0)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )  # e.g., "groceries", "tax"
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    # Each line item can be assigned to a different budget
    budget_id: Mapped[int | None] = mapped_column(
        ForeignKey("budget.id"),
        nullable=True,
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    parent_transaction: Mapped["SimpleFinTransaction"] = relationship(
        back_populates="line_items",
    )
    budget: Mapped[Optional["Budget"]] = relationship()
