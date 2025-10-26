"""SimpleFin account model for financial account data."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from finance_api.models.db import Base

if TYPE_CHECKING:
    from finance_api.models.organization import SimpleFinOrganization
    from finance_api.models.transaction import (
        SimpleFinTransaction,
    )  # Import only for type checking
    from finance_api.models.user import User


class SimpleFinAccount(Base):
    """SimpleFin account model representing a financial account."""

    __tablename__ = "simplefin_account"
    """Note: account_id is the ID from SimpleFin, not guaranteed to be unique, use
    (org_domain, account_id) to uniquely identify an account"""
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    account_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        server_default=None,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="",
        default="",
    )
    currency: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="",
        default="",
    )
    balance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.0",
        default=0.0,
    )
    available_balance: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        server_default=None,
        default=None,
    )
    balance_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )  # When the balance and available_balance was last updated
    possible_error: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="false",
        default=False,
    )
    extra: Mapped[dict] = mapped_column(
        JSONB,
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
    transactions: Mapped[list["SimpleFinTransaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    org_domain: Mapped[int] = mapped_column(
        ForeignKey("simplefin_organization.domain"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    org: Mapped["SimpleFinOrganization"] = relationship(back_populates="accounts")
    user: Mapped["User"] = relationship(back_populates="accounts")
