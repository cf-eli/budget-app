"""User model for application users."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finance_api.models.db import Base

if TYPE_CHECKING:
    from finance_api.models.account import (
        SimpleFinAccount,
    )
    from finance_api.models.budget import Budget


class User(Base):
    """User model representing an application user."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    auth_user_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )
    access_url: Mapped[str] = mapped_column(String, nullable=True, server_default=None)

    accounts: Mapped[list["SimpleFinAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
