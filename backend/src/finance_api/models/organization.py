"""SimpleFin organization model for financial institutions."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
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


class SimpleFinOrganization(Base):
    """SimpleFin organization model representing a financial institution."""

    __tablename__ = "simplefin_organization"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    domain: Mapped[str] = mapped_column(
        String,
        server_default=None,
        nullable=False,
        unique=True,
        index=True,
    )  # guaranteed to be unique, use as primary identifier
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="",
        default="",
    )
    sfin_url: Mapped[str] = mapped_column(String, server_default=None, nullable=False)
    url: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="",
        default="",
    )
    org_id: Mapped[str] = mapped_column(
        String,
        server_default=None,
        nullable=False,
    )  # Organization ID from SimpleFin, not guaranteed to be unique

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    accounts: Mapped[list["SimpleFinAccount"]] = relationship(
        back_populates="org",
        cascade="all, delete-orphan",
    )
