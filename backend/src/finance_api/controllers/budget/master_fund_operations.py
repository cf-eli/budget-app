"""
Fund Master mutation endpoints.

Endpoints for combining, unlinking, discontinuing, and managing fund masters.
"""

from litestar import post, status_codes

from finance_api.crud.budget import (
    add_fund_to_orphaned_master,
    apply_fund_increments,
    combine_fund_masters,
    discontinue_fund_master,
    unlink_fund_and_split_master,
)
from finance_api.models.db import get_session
from finance_api.models.user import User
from finance_api.schemas import budget
from finance_api.schemas.exceptions import FinanceServerError
from finance_api.schemas.schema import MessageResponse


@post(
    "/funds/{fund_id:int}/combine",
    response=MessageResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def combine_fund_to_master(
    fund_id: int,
    data: budget.FundCombineRequest,
) -> MessageResponse:
    """
    Combine a fund with another fund's master.

    This combines the fund masters of two funds, merging their balances.
    All funds from the source master will be pointed to the target master.

    This is useful for the edge case where a user creates a new fund manually
    and wants to add it to an existing master fund family (instead of copying
    from the previous month).

    Args:
        fund_id: ID of the source fund (its master will be merged)
        data: Request containing target_fund_id

    Returns:
        Success message with combination details

    Raises:
        ValueError: If funds are invalid or already in same master

    """
    result = await combine_fund_masters(fund_id, data.target_fund_id)
    combined = result["combined_balance"]
    msg = f"Funds combined successfully. Combined balance: ${combined:.2f}"
    return MessageResponse(message=msg)


@post(
    "/funds/{fund_id:int}/unlink",
    response=MessageResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def unlink_fund(
    fund_id: int,
    data: budget.FundUnlinkRequest,
) -> MessageResponse:
    """
    Unlink a fund from its master and create a new master with specified balance.

    Args:
        fund_id: ID of the fund to unlink
        data: Request containing keep_amount

    Returns:
        Success message with split details

    Raises:
        ValueError: If keep_amount exceeds master balance

    """
    result = await unlink_fund_and_split_master(fund_id, data.keep_amount)
    new_balance = result["new_master_balance"]
    msg = f"Fund unlinked successfully. New master balance: ${new_balance:.2f}"
    return MessageResponse(message=msg)


@post(
    "/funds/apply-increments",
    status_code=status_codes.HTTP_200_OK,
)
async def apply_fund_increments_endpoint(
    user: User,
    data: budget.ApplyFundIncrementsRequest,
) -> budget.ApplyFundIncrementsResponse:
    """
    Apply fund increments to total_amount for all funds in a month.

    This manually adds each fund's increment to its total_amount, by priority,
    and propagates changes to future linked funds.

    Request Body:
        {
            "month": 11,
            "year": 2025,
            "safe_mode": false
        }

    Response:
        {
            "applied_funds": [
                {"fund_id": 1, "fund_name": "Emergency", "amount_added": 500}
            ],
            "skipped_funds": [
                {"fund_id": 2, "fund_name": "Vacation", "reason": "Max reached"}
            ],
            "balance_before": 2000,
            "balance_after": 1000,
            "total_applied": 1000,
            "would_go_negative": false
        }

    Returns:
        ApplyFundIncrementsResponse with details of applied and skipped funds

    """
    async with get_session() as sess:
        result = await apply_fund_increments(
            user_id=user.id,
            month=data.month,
            year=data.year,
            safe_mode=data.safe_mode,
            session=sess,
        )

        return budget.ApplyFundIncrementsResponse(**result)


@post(
    "/funds/masters/{master_id:int}/discontinue",
    response=MessageResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def discontinue_master_endpoint(
    user: User,
    master_id: int,
    data: budget.DiscontinueMasterRequest,
) -> MessageResponse:
    """
    Discontinue a fund master by withdrawing its balance.

    Args:
        user: The authenticated user
        master_id: Master fund ID to discontinue
        data: Request with month, year

    Returns:
        Success message

    Raises:
        ValueError: If master not found or already has fund for this month

    """
    result = await discontinue_fund_master(
        master_fund_id=master_id,
        month=data.month,
        year=data.year,
        user_id=user.id,
    )
    withdrawal = abs(result["withdrawal_amount"])
    msg = f"Fund master discontinued. Withdrawal amount: ${withdrawal:.2f}"
    return MessageResponse(message=msg)


@post(
    "/funds/masters/{master_id:int}/add-month",
    response=MessageResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def add_month_to_master_endpoint(
    user: User,
    master_id: int,
    data: budget.AddMonthToMasterRequest,
) -> MessageResponse:
    """
    Add a fund to an orphaned master for the specified month.

    Args:
        user: The authenticated user
        master_id: Orphaned master fund ID
        data: Request with month, year, priority, increment

    Returns:
        Success message

    Raises:
        ValueError: If master not found or fund already exists for this month

    """
    try:
        result = await add_fund_to_orphaned_master(
            master_fund_id=master_id,
            month=data.month,
            year=data.year,
            user_id=user.id,
            priority=data.priority,
            increment=data.increment,
            max_amount=data.max,
        )
        return MessageResponse(
            message=f"Fund added to master. Balance: ${result['master_balance']:.2f}",
        )
    except ValueError as e:
        msg = f"Failed to add fund to master: {e!s}"
        raise FinanceServerError(msg) from e
