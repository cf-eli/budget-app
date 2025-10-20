from litestar import post, status_codes, Request, Router, get
from typing import Dict
from finance_api.crud.user import ensure_user
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException
from finance_api.schemas.budget import BudgetRequest, BudgetNameResponse, AllBudgetsResponse
from finance_api.crud import budget as budget_crud
from finance_api.crud.transaction import assign_transaction_to_budget

@post("/create", response=dict, status_code=status_codes.HTTP_201_CREATED)
async def create_budget(request: Request, data: BudgetRequest) -> Dict[str, str]:
    """Create a new budget.

    This endpoint creates a new budget based on the provided details.
    It accepts a JSON payload with the budget details and returns the ID of the created budget.

    Returns:
        A dictionary containing the ID of the created budget.
    """

    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {"id": "A user"}  # For testing purposes when auth is disabled
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
        raise ValueError("Invalid budget type")  # TODO better exception handler
    return {"message": "Budget created successfully"}


@post(
    "/{budget_id:int}/transactions/{transaction_id:int}",
    response=dict,
    status_code=status_codes.HTTP_200_OK,
)
async def add_transaction_to_budget(
    request: Request, budget_id: int, transaction_id: int
) -> Dict[str, str]:
    """Add a transaction to a budget.

    This endpoint adds a transaction to the specified budget.
    Args:
        budget_id (str): The ID of the budget.
        transaction_id (str): The ID of the transaction to add.
    Returns:
        A dictionary confirming the addition of the transaction to the budget.
    """

    await assign_transaction_to_budget(transaction_id, budget_id)
    return {"message": "Transaction added to budget"}


@get("/all", response=dict, status_code=status_codes.HTTP_200_OK)
async def get_all_budgets(request: Request) -> AllBudgetsResponse:
    """Get all budgets for the authenticated user.

    This endpoint retrieves all budgets associated with the authenticated user.
    Returns:
        A dictionary containing all budgets for the user.

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {"id": "A user"}  # For testing purposes when auth is disabled
    user = await ensure_user(request_user["id"])
    if not user:
        raise Exception("User not found")  # TODO Change to proper exception handling
    budgets = await budget_crud.get_budgets(user.id)
    budgets = AllBudgetsResponse.model_validate(budgets)
    return budgets


@get("/names", response=list[BudgetNameResponse], status_code=status_codes.HTTP_200_OK)
async def get_budgets_names(request: Request) -> list[BudgetNameResponse]:
    """Get all budget IDs and names for the authenticated user.

    This endpoint retrieves all budget IDs and names associated with the authenticated user.
    Returns:
        A list of dictionaries containing budget IDs and names.

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {"id": "A user"}  # For testing purposes when auth is disabled
    user = await ensure_user(request_user["id"])
    if not user:
        raise Exception("User not found")  # TODO Change to proper exception handling
    budgets = await budget_crud.get_budgets_name()
    budgets = [BudgetNameResponse.model_validate(b) for b in budgets]
    return budgets




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
# @plaid_route.post("/budgets/add_transaction")
# async def create_budget_transaction_post(request: AddTransaction):
#     create_budget_transaction(request.budget_id, request.transaction_id)
#     return {"message": "Transaction added to budget"}
