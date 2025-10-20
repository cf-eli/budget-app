from pydantic import BaseModel, ConfigDict, Field, field_validator, BeforeValidator, model_validator
from typing import List, Optional, Union, Dict
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

def timestamp_to_utc(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def kebab_to_snake(name: str) -> str:
    return name.replace("_", "-")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=kebab_to_snake,
        populate_by_name=True,
        from_attributes=True,
    )



class Organization(BaseSchema):
    id: str
    domain: str
    sfin_url: str
    url: str = ""
    name: str = ""




class Transaction(BaseSchema):
    id: str
    posted: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    amount: float
    description: str
    payee: str
    memo: str
    transacted_at: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    pending: Optional[bool] = False

    @field_validator("amount", mode='before') # TODO: two seperate instance of this function doing same thing, combine into one
    def convert_to_float(cls, value):
        if value is None:
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Expected a number for {value}, got {type(value).__name__}")



class Holding(BaseSchema):
    """Holding data."""

    id: str
    created: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    currency: Optional[str]
    cost_basis: str
    description: str
    market_value: str
    purchase_price: str
    shares: str
    symbol: str

    # @field_validator("created", mode='before')
    # def convert_timestamp(cls, value):
    #     if isinstance(value, (int, float)):
    #         return timestamp_to_utc(value)
    #     return value


class Account(BaseSchema):
    org: Organization
    id: str
    name: str
    currency: str
    balance: float
    available_balance: Optional[float]
    balance_date: Annotated[datetime, BeforeValidator(timestamp_to_utc)]
    transactions: List[Transaction]
    holdings: List[Holding] = Field(default_factory=list)
    extra: Optional[Dict] = None
    possible_error: bool = False

    @field_validator("balance", "available_balance", mode='before')
    def convert_to_float(cls, value):
        if value is None:
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Expected a number for {value}, got {type(value).__name__}")



class FinancialData(BaseSchema):
    """Financial Data."""

    errors: List[str]
    x_api_message: List[str] = Field(default_factory=list)
    accounts: List[Account] = Field(default_factory=list)

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
    token: str