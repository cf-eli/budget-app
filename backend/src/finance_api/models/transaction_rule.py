"""Transaction rule model for automated budget assignment."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finance_api.models.db import Base

if TYPE_CHECKING:
    from finance_api.models.budget import Budget
    from finance_api.models.user import User


class TransactionRule(Base):
    """
    Rule for automatically assigning transactions to budgets.

    Rules contain conditions that are matched against transaction attributes.
    All conditions must match (AND logic) for a rule to apply.
    Rules are applied in priority order (lower number = higher priority).
    """

    __tablename__ = "transaction_rule"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Lower priority number = higher priority (applied first)
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Target budget to assign matching transactions to
    target_budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Conditions stored as JSON array of condition objects
    conditions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    # User who owns this rule
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="transaction_rules")
    target_budget: Mapped[Optional["Budget"]] = relationship()
