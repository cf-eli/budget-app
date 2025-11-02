"""Budget management endpoints."""

from litestar import post, status_codes
from litestar.exceptions import NotFoundException

from finance_api.constants import MAX_MONTH, MAX_YEAR, MIN_MONTH, MIN_YEAR
from finance_api.crud import budget as budget_crud
from finance_api.crud.transaction import assign_transaction_to_budget
from finance_api.models.user import User
from finance_api.schemas.budget import (
    BudgetRequest,
    CopyBudgetsRequest,
    CopyBudgetsResponse,
)
from finance_api.schemas.exceptions import FinanceServerError
from finance_api.schemas.schema import MessageResponse


@post("/create", response=MessageResponse, status_code=status_codes.HTTP_201_CREATED)
async def create_budget(user: User, data: BudgetRequest) -> MessageResponse:
    """
    Create a new budget.

    This endpoint creates a new budget based on the provided details.
    It accepts a JSON payload with the budget details and returns the
      ID of the created budget.

    Returns:
        A dictionary containing the ID of the created budget.

    """
    if data.budget_type == "income":
        await budget_crud.create_income(
            user_id=user.id,
            name=data.name,
            fixed=data.fixed,
            expected_amount=data.expected_amount,
            min_amount=data.min,
            max_amount=data.max,
            month=data.month,
            year=data.year,
        )
    elif data.budget_type == "expense":
        await budget_crud.create_expense(
            user_id=user.id,
            name=data.name,
            fixed=data.fixed,
            flexible=data.flexible,
            expected_amount=data.expected_amount,
            min_amount=data.min,
            max_amount=data.max,
            month=data.month,
            year=data.year,
        )
    elif data.budget_type == "fund":
        await budget_crud.create_fund(
            user_id=user.id,
            name=data.name,
            increment=data.increment,
            priority=data.priority,
            max_amount=data.max,
            month=data.month,
            year=data.year,
            master_fund_id=data.master_fund_id,  # Optional: link to existing master
        )
    else:
        msg = "Invalid budget type"
        raise ValueError(msg)  # TODO(cf-eli): #004 better exception handler
    return MessageResponse(message="Budget created successfully")


@post(
    "/{budget_id:int}/transactions/{transaction_id:int}",
    response=MessageResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def add_transaction_to_budget(
    budget_id: int,
    transaction_id: int,
) -> MessageResponse:
    """
    Add a transaction to a budget.

    This endpoint adds a transaction to the specified budget.

    Args:
        budget_id: The ID of the budget.
        transaction_id: The ID of the transaction to add.

    Returns:
        A dictionary confirming the addition of the transaction to the budget.

    """
    await assign_transaction_to_budget(transaction_id, budget_id)
    return MessageResponse(message="Transaction added to budget")


@post(
    "/copy-from-previous",
    response=CopyBudgetsResponse,
    status_code=status_codes.HTTP_201_CREATED,
)
async def copy_budgets_from_previous(
    user: User,
    data: CopyBudgetsRequest,
) -> CopyBudgetsResponse:
    """
    Copy all budgets from the previous month to the target month.

    This endpoint copies all budget configurations (income, expenses, flexible, funds)
    from the previous month to a new target month. It validates that the target month
    is empty and that the previous month has budgets to copy.

    Args:
        user: The authenticated user
        data: Request containing target_month and target_year

    Returns:
        Response with counts of copied budgets and source month info

    Raises:
        NotFoundException: If no budgets found in previous month (404)
        ConflictException: If target month already has budgets (409)
        BadRequestException: If month/year values are invalid (400)

    """
    # Validate request parameters
    _validate_copy_request(data)

    try:
        result = await budget_crud.copy_budgets_from_previous_month(
            user_id=user.id,
            target_month=data.target_month,
            target_year=data.target_year,
            source_month=data.source_month,
            source_year=data.source_year,
        )
        return CopyBudgetsResponse.model_validate(result)
    except ValueError as e:
        _handle_copy_error(e)


def _validate_month(month: int, field_name: str = "Month") -> None:
    """Validate month is within valid range."""
    if not MIN_MONTH <= month <= MAX_MONTH:
        msg = f"{field_name} must be between {MIN_MONTH} and {MAX_MONTH}"
        raise ValueError(msg)


def _validate_year(year: int, field_name: str = "Year") -> None:
    """Validate year is within valid range."""
    if year < MIN_YEAR or year > MAX_YEAR:
        msg = f"{field_name} must be between {MIN_YEAR} and {MAX_YEAR}"
        raise ValueError(msg)


def _validate_copy_request(data: CopyBudgetsRequest) -> None:
    """Validate month and year values in copy request."""
    # Validate target month and year
    _validate_month(data.target_month, "Month")
    _validate_year(data.target_year, "Year")

    # Validate source month/year if provided
    if data.source_month is not None and not (
        MIN_MONTH <= data.source_month <= MAX_MONTH
    ):
        msg = f"Source month must be between {MIN_MONTH} and {MAX_MONTH}"
        raise ValueError(msg)
    if data.source_year is not None and (
        data.source_year < MIN_YEAR or data.source_year > MAX_YEAR
    ):
        msg = f"Source year must be between {MIN_YEAR} and {MAX_YEAR}"
        raise ValueError(msg)


def _handle_copy_error(error: ValueError) -> None:
    """Handle errors from copy operation and raise appropriate exceptions."""
    error_msg = str(error)
    if "already has budgets" in error_msg:
        # TODO(cf-eli): #004 Use ConflictException when available
        msg = f"Target month already has budgets: {error_msg}"
        raise FinanceServerError(msg) from error
    if "No budgets found" in error_msg:
        msg = f"No budgets found in source month: {error_msg}"
        raise NotFoundException(msg) from error
    # Re-raise any other ValueError
    msg = f"Error copying budgets: {error_msg}"
    raise ValueError(msg) from error
