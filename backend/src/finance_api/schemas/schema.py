"""Data schemas for the finance API."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)


def timestamp_to_utc(ts: float) -> datetime:
    """Convert Unix timestamp to UTC datetime."""
    return datetime.fromtimestamp(ts, tz=UTC)


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case to snake_case."""
    return name.replace("_", "-")

def convert_to_float(value: None | float) -> float | None:
    """Convert value to float, handling None."""
    if value is None:
        return value
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        msg = f"Expected a number for {value}, got {type(value).__name__}"
        raise ValueError(
            msg,
        ) from e

class BaseSchema(BaseModel):
    """Base schema with common configuration for kebab-case to snake_case conversion."""

    model_config = ConfigDict(
        alias_generator=kebab_to_snake,
        populate_by_name=True,
        from_attributes=True,
    )


class Organization(BaseSchema):
    """Schema for financial organization data."""

    id: str
    domain: str
    sfin_url: str
    url: str = ""
    name: str = ""


class Transaction(BaseSchema):
    """Schema for financial transaction data."""

    id: str
    posted: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    amount: Annotated[float, BeforeValidator(convert_to_float)]
    description: str
    payee: str
    memo: str
    transacted_at: Annotated[datetime | float, BeforeValidator(timestamp_to_utc)]
    pending: bool | None = False


class Holding(BaseSchema):
    """Holding data."""

    id: str
    created: Annotated[datetime | float, BeforeValidator(timestamp_to_utc)]
    currency: str | None
    cost_basis: str
    description: str
    market_value: str
    purchase_price: str
    shares: str
    symbol: str


class Account(BaseSchema):
    """Schema for financial account data with transactions and holdings."""

    org: Organization
    id: str
    name: str
    currency: str
    balance: Annotated[float, BeforeValidator(convert_to_float)]
    available_balance: Annotated[float | None, BeforeValidator(convert_to_float)]
    balance_date: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    transactions: list[Transaction]
    holdings: list[Holding] = Field(default_factory=list)
    extra: dict | None = None
    possible_error: bool = False


class FinancialData(BaseSchema):
    """Financial Data."""

    errors: list[str]
    x_api_message: list[str] = Field(default_factory=list)
    accounts: list[Account] = Field(default_factory=list)

    @model_validator(mode="after")
    def set_possible_errors(self) -> "FinancialData":
        """Set the `possible_error` flag for accounts based on errors."""
        error_account_names = [
            a.replace("Connection to ", "").replace(" may need attention", "")
            for a in self.errors
        ]

        for account in self.accounts:
            if account.org.name in error_account_names:
                account.possible_error = True

        return self


class TokenRequest(BaseModel):
    """Request schema for authentication token."""

    token: str


class MessageResponse(BaseModel):
    """Response schema for simple message responses."""

    message: str


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
