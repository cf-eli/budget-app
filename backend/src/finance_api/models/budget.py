"""Budget models for income, expenses, and funds."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finance_api.models.db import Base

if TYPE_CHECKING:
    from finance_api.models.transaction import (
        SimpleFinTransaction,
    )  # Import only for type checking
    from finance_api.models.user import User


class Budget(Base):
    """Budget model representing a budget category."""

    __tablename__ = "budget"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    enable: Mapped[bool | None] = mapped_column(Boolean, default=True)
    deleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    transactions: Mapped[list["SimpleFinTransaction"]] = relationship(
        back_populates="budget",
    )
    user: Mapped["User"] = relationship(back_populates="budgets")


class Income(Base):
    """Income budget model for expected income sources."""

    __tablename__ = "income"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    fixed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min: Mapped[float | None] = mapped_column(Float, nullable=True)
    max: Mapped[float | None] = mapped_column(Float, nullable=True)


class Expense(Base):
    """Expense budget model for expense categories."""

    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    fixed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    flexible = mapped_column(Boolean, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min: Mapped[float | None] = mapped_column(Float, nullable=True)
    max: Mapped[float | None] = mapped_column(Float, nullable=True)


class FundMaster(Base):
    """
    Fund master model tracking cumulative balance across linked funds.

    Each fund points to a master, and linking funds means pointing to the same master.
    The master tracks the total balance across all months for a "fund family".
    """

    __tablename__ = "fund_masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )  # Optional "fund family" name
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now,
        server_default=func.now(),
    )

    # Relationship
    funds: Mapped[list["Fund"]] = relationship(back_populates="master_fund")


class Fund(Base):
    """
    Fund budget model for savings funds with master fund tracking.

    master_fund_id: Links to FundMaster for balance continuity
        (which funds share balance)
    month_amount: Amount added/allocated this specific month only

    Note: Fund identity across months is tracked implicitly through
        master_fund_id. When copying budgets, funds automatically link
        to their source fund's master.
    """

    __tablename__ = "fund"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    increment: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    month_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    max: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Link to master fund for balance tracking
    master_fund_id: Mapped[int] = mapped_column(
        ForeignKey("fund_masters.id"),
        nullable=False,
    )

    # Relationships
    master_fund: Mapped["FundMaster"] = relationship(back_populates="funds")
