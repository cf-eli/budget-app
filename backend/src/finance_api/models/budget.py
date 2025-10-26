"""Budget models for income, expenses, and funds."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
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


class Fund(Base):
    """Fund budget model for savings funds."""

    __tablename__ = "fund"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    increment: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
    )
    max: Mapped[float | None] = mapped_column(Float, nullable=True)
