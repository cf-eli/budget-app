"""Budget management endpoints."""

from litestar import Request, Router, get, post, status_codes
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException

from finance_api.config import settings
from finance_api.crud import budget as budget_crud
from finance_api.crud.transaction import assign_transaction_to_budget
from finance_api.crud.user import ensure_user
from finance_api.schemas.budget import (
    AllBudgetsResponse,
    BudgetNameResponse,
    BudgetRequest,
)
from finance_api.schemas.exceptions import FinanceServerError
from finance_api.schemas.schema import MessageResponse


@post("/create", response=MessageResponse, status_code=status_codes.HTTP_201_CREATED)
async def create_budget(request: Request, data: BudgetRequest) -> MessageResponse:
    """
    Create a new budget.

    This endpoint creates a new budget based on the provided details.
    It accepts a JSON payload with the budget details and returns the
      ID of the created budget.

    Returns:
        A dictionary containing the ID of the created budget.

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {
            "id": settings.dev_default_user_id,
        }  # For testing purposes when auth is disabled
    user = await ensure_user(request_user["id"])

    if data.budget_type == "income":
        await budget_crud.create_income(
            user_id=user.id,
            name=data.name,
            fixed=data.fixed,
            expected_amount=data.expected_amount,
            min_amount=data.min,
            max_amount=data.max,
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
        )
    elif data.budget_type == "fund":
        await budget_crud.create_fund(
            user_id=user.id,
            name=data.name,
            increment=data.increment,
            priority=data.priority,
            max_amount=data.max,
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


@get("/all", response=AllBudgetsResponse, status_code=status_codes.HTTP_200_OK)
async def get_all_budgets(
    request: Request,
    month: int | None = None,
    year: int | None = None,
) -> AllBudgetsResponse:
    """
    Get all budgets for the authenticated user.

    This endpoint retrieves all budgets associated with the authenticated user.

    Args:
        request: The HTTP request object
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        A dictionary containing all budgets for the user.

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {
            "id": settings.dev_default_user_id,
        }  # For testing purposes when auth is disabled
    user = await ensure_user(request_user["id"])
    if not user:
        msg = "User not found"
        raise FinanceServerError(msg)
        # TODO(cf-eli): #004 Change to proper exception handling
    budgets = await budget_crud.get_budgets(user.id, month=month, year=year)
    return AllBudgetsResponse.model_validate(budgets)


@get("/names", response=list[BudgetNameResponse], status_code=status_codes.HTTP_200_OK)
async def get_budgets_names(
    request: Request,
    month: int | None = None,
    year: int | None = None,
) -> list[BudgetNameResponse]:
    """
    Get all budget IDs and names for the authenticated user.

    This endpoint retrieves all budget IDs and names associated
      with the authenticated user.

    Args:
        request: The HTTP request object
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        A list of dictionaries containing budget IDs and names.

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {
            "id": settings.dev_default_user_id,
        }  # For testing purposes when auth is disabled
    user = await ensure_user(request_user["id"])
    if not user:
        msg = "User not found"
        # TODO(cf-eli): #004 Change to proper exception handling
        raise FinanceServerError(msg)
    budgets = await budget_crud.get_budgets_name(
        user_id=user.id,
        month=month,
        year=year,
    )
    return [BudgetNameResponse.model_validate(b) for b in budgets]


budget_router = Router(
    path="/api/v1/budgets",
    route_handlers=[
        create_budget,
        add_transaction_to_budget,
        get_all_budgets,
        get_budgets_names,
    ],
    tags=["Budget"],
)
