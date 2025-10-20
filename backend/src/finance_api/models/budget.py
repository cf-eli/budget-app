from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Float,
    JSON,
    ForeignKey,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from finance_api.models.db import Base
from typing import Optional, List

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finance_api.models.user import User
    from finance_api.models.transaction import (
        SimpleFinTransaction,
    )  # Import only for type checking


class Budget(Base):
    __tablename__ = "budget"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    enable: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    deleted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    transactions: Mapped[List["SimpleFinTransaction"]] = relationship(
        back_populates="budget",
    )
    user: Mapped["User"] = relationship(back_populates="budgets")

class Income(Base):
    __tablename__ = "income"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    fixed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    fixed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    flexible = mapped_column(Boolean, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Float, nullable=False)
    min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Fund(Base):
    __tablename__ = "fund"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("budget.id"), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    increment: Mapped[float] = mapped_column(Float, nullable=False)
    current_amount: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # TODO: change nullable to true and default to 0
    max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


# class BudgetTransactions(Base):
#     __tablename__ = "budget_transactions"

#     budget_id: Mapped[int] = mapped_column(Integer, ForeignKey("budgets.id"), primary_key=True)
#     transaction_id: Mapped[str] = mapped_column(
#         String, ForeignKey("plaid_transactions.transaction_id"), primary_key=True
#     )

    # budget: Mapped["Budget"] = relationship("Budget", back_populates="transactions")
    # transaction: Mapped["PlaidTransaction"] = relationship(
    #     "PlaidTransaction", back_populates="budget_transactions"
    # )
