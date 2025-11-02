"""
Fund Master query endpoints.

Endpoints for retrieving fund master information and calculations.
"""

from litestar import get, status_codes

from finance_api.crud.budget import (
    calculate_fund_balance,
    get_fund_by_id,
    get_master_fund_details,
    get_orphaned_fund_masters,
)
from finance_api.models.db import get_session
from finance_api.models.user import User
from finance_api.schemas import budget


@get(
    "/funds/{fund_id:int}/calculate",
    response=budget.FundCalculationResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def calculate_fund(
    fund_id: int,
) -> budget.FundCalculationResponse:
    """
    Calculate the dynamic balance for a fund.

    This endpoint calculates the fund's balance by traversing backward through
    linked funds and summing transactions and allocated carryover amounts.

    Args:
        fund_id: ID of the fund to calculate

    Returns:
        Fund calculation details with breakdown

    Raises:
        NotFoundException: If fund not found

    """
    # Get fund details from CRUD layer
    fund_data = await get_fund_by_id(fund_id)

    # Calculate balance using master fund system
    async with get_session() as sess:
        calc_result = await calculate_fund_balance(fund_id, session=sess)

    # Build response
    return budget.FundCalculationResponse(
        fund_id=fund_data["id"],
        name=fund_data["name"],
        priority=fund_data["priority"],
        increment=fund_data["increment"],
        max=fund_data["max"],
        master_balance=calc_result["master_balance"],
        month_amount=fund_data["month_amount"],
        calculated_amount=calc_result["total_balance"],
        transactions=calc_result["transactions"],
        breakdown=[
            budget.FundCalculationBreakdown(**item) for item in calc_result["breakdown"]
        ],
        master_id=fund_data["master_fund_id"],
    )


@get(
    "/funds/masters/{master_id:int}/details",
    response=budget.MasterFundDetailsResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def get_master_fund_details_endpoint(
    user: User,
    master_id: int,
) -> budget.MasterFundDetailsResponse:
    """
    Get detailed information about a master fund and all associated funds.

    Returns master fund total balance and list of all funds linked to this master with:
    - Month/year
    - Amount contributed (month_amount)
    - Amount withdrawn (sum of transactions)
    - Net contribution (month_amount + transactions)

    Args:
        user: The authenticated user
        master_id: Master fund ID

    Returns:
        Master fund details with all associated funds

    Raises:
        NotFoundException: If master not found or user doesn't own funds

    """
    details = await get_master_fund_details(
        master_id=master_id,
        user_id=user.id,
    )
    return budget.MasterFundDetailsResponse.model_validate(details)


@get(
    "/funds/orphaned-masters",
    response=budget.OrphanedMastersResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def get_orphaned_masters_endpoint(
    user: User,
    month: int,
    year: int,
) -> budget.OrphanedMastersResponse:
    """
    Get orphaned fund masters with balance > 0 but no fund for specified month.

    Args:
        user: The authenticated user
        month: The month (1-12)
        year: The year

    Returns:
        List of orphaned masters

    """
    result = await get_orphaned_fund_masters(
        user_id=user.id,
        month=month,
        year=year,
    )

    return budget.OrphanedMastersResponse(orphaned_masters=result)
