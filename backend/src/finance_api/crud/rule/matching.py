"""Rule condition matching logic."""

from finance_api.models.transaction import SimpleFinTransaction
from finance_api.schemas.rules import (
    RuleCondition,
    RuleFieldEnum,
    RuleOperatorEnum,
)


def get_field_value(
    transaction: SimpleFinTransaction,
    field: RuleFieldEnum,
) -> str | float:
    """Extract the field value from a transaction based on field type."""
    field_map = {
        RuleFieldEnum.PAYEE: transaction.payee or "",
        RuleFieldEnum.DESCRIPTION: transaction.description or "",
        RuleFieldEnum.AMOUNT: transaction.amount,
        RuleFieldEnum.ACCOUNT_ID: transaction.account_id,
        RuleFieldEnum.ACCOUNT_NAME: (
            transaction.account.name if transaction.account else ""
        ),
        RuleFieldEnum.ORG_DOMAIN: (
            transaction.account.org.domain
            if transaction.account and transaction.account.org
            else ""
        ),
        RuleFieldEnum.ORG_NAME: (
            transaction.account.org.name
            if transaction.account and transaction.account.org
            else ""
        ),
    }
    return field_map.get(field, "")


def apply_text_operator(
    field_value: str | float,
    condition: RuleCondition,
) -> bool:
    """Apply text-based operators (exact, contains)."""
    if condition.operator == RuleOperatorEnum.EXACT:
        return str(field_value).lower() == str(condition.value).lower()
    if condition.operator == RuleOperatorEnum.CONTAINS:
        return str(condition.value).lower() in str(field_value).lower()
    return False


def apply_numeric_operator(
    field_value: str | float,
    condition: RuleCondition,
) -> bool:
    """Apply numeric operators (greater_than, less_than, range)."""
    try:
        numeric_value = float(field_value)  # type: ignore[arg-type]
        if condition.operator == RuleOperatorEnum.GREATER_THAN:
            return numeric_value > float(condition.value)
        if condition.operator == RuleOperatorEnum.LESS_THAN:
            return numeric_value < float(condition.value)
        if condition.operator == RuleOperatorEnum.RANGE:
            return (
                float(condition.value)
                <= numeric_value
                <= float(
                    condition.value2 or 0,
                )
            )
    except (TypeError, ValueError):
        return False
    return False


def matches_condition(
    transaction: SimpleFinTransaction,
    condition: RuleCondition,
) -> bool:
    """Check if a transaction matches a single condition."""
    field_value = get_field_value(transaction, condition.field)

    # Text operators
    if condition.operator in (
        RuleOperatorEnum.EXACT,
        RuleOperatorEnum.CONTAINS,
    ):
        return apply_text_operator(field_value, condition)

    # Numeric operators
    return apply_numeric_operator(field_value, condition)


def matches_all_conditions(
    transaction: SimpleFinTransaction,
    conditions: list[dict],
) -> bool:
    """Check if a transaction matches ALL conditions (AND logic)."""
    for cond_dict in conditions:
        condition = RuleCondition(**cond_dict)
        if not matches_condition(transaction, condition):
            return False
    return True
