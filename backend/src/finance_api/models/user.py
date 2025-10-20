from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from finance_api.models.db import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from finance_api.models.account import (
        SimpleFinAccount,
    )
    from finance_api.models.budget import Budget


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )

    auth_user_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    access_url: Mapped[str] = mapped_column(String, nullable=True, server_default=None)
    
    accounts: Mapped[List["SimpleFinAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )