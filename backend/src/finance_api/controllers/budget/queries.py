"""Budget query endpoints."""

from litestar import get, status_codes

from finance_api.crud import budget as budget_crud
from finance_api.models.user import User
from finance_api.schemas.budget import AllBudgetsResponse, BudgetNameResponse


@get("/all", response=AllBudgetsResponse, status_code=status_codes.HTTP_200_OK)
async def get_all_budgets(
    user: User,
    month: int | None = None,
    year: int | None = None,
) -> AllBudgetsResponse:
    """
    Get all budgets for the authenticated user.

    This endpoint retrieves all budgets associated with the authenticated user.

    Args:
        user: The authenticated user
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        A dictionary containing all budgets for the user.

    """
    budgets = await budget_crud.get_budgets(user.id, month=month, year=year)
    return AllBudgetsResponse.model_validate(budgets)


@get("/names", response=list[BudgetNameResponse], status_code=status_codes.HTTP_200_OK)
async def get_budgets_names(
    user: User,
    month: int | None = None,
    year: int | None = None,
) -> list[BudgetNameResponse]:
    """
    Get all budget IDs and names for the authenticated user.

    This endpoint retrieves all budget IDs and names associated
      with the authenticated user.

    Args:
        user: The authenticated user
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        A list of dictionaries containing budget IDs and names.

    """
    budgets = await budget_crud.get_budgets_name(
        user_id=user.id,
        month=month,
        year=year,
    )
    return [BudgetNameResponse.model_validate(b) for b in budgets]
