"""
Fund Master operations.

Functions for combining and unlinking fund masters.
These are the primary active operations on fund masters.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.models.budget import Budget, Fund, FundMaster
from finance_api.models.db import get_session


async def combine_fund_masters(
    source_fund_id: int,
    target_fund_id: int,
    session: AsyncSession | None = None,
) -> dict:
    """
    Combine two fund masters by merging their balances.

    All funds from the source master will be pointed to the target master,
    and the source master will be deleted. This is useful when a user creates
    a new fund manually and wants to add it to an existing master fund family.

    Args:
        source_fund_id: ID of source fund (its master will be merged)
        target_fund_id: ID of target fund (its master will be kept)
        session: Optional database session

    Returns:
        Dict with combined master info

    Raises:
        ValueError: If funds don't exist or are already in same master

    """
    async with get_session(session) as sess:
        # Get both funds with their masters
        source_query = (
            select(Fund.id, Fund.master_fund_id, FundMaster.total_amount, Budget.name)
            .join(FundMaster, Fund.master_fund_id == FundMaster.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.id == source_fund_id)
        )
        source_result = await sess.execute(source_query)
        source_data = source_result.first()

        if not source_data:
            msg = f"Source fund {source_fund_id} not found"
            raise ValueError(msg)

        target_query = (
            select(Fund.id, Fund.master_fund_id, FundMaster.total_amount, Budget.name)
            .join(FundMaster, Fund.master_fund_id == FundMaster.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.id == target_fund_id)
        )
        target_result = await sess.execute(target_query)
        target_data = target_result.first()

        if not target_data:
            msg = f"Target fund {target_fund_id} not found"
            raise ValueError(msg)

        # Check if already in same master
        if source_data.master_fund_id == target_data.master_fund_id:
            msg = "Funds are already in the same master fund family"
            raise ValueError(msg)

        # Get master objects
        target_master_stmt = select(FundMaster).where(
            FundMaster.id == target_data.master_fund_id,
        )
        target_master_result = await sess.execute(target_master_stmt)
        target_master = target_master_result.scalar_one()

        source_master_stmt = select(FundMaster).where(
            FundMaster.id == source_data.master_fund_id,
        )
        source_master_result = await sess.execute(source_master_stmt)
        source_master = source_master_result.scalar_one()

        # Add source master's balance to target master
        combined_balance = target_master.total_amount + source_master.total_amount
        target_master.total_amount = combined_balance

        # Point all funds from source master to target master
        update_funds_stmt = select(Fund).where(
            Fund.master_fund_id == source_data.master_fund_id,
        )
        funds_to_update_result = await sess.execute(update_funds_stmt)
        funds_to_update = funds_to_update_result.scalars().all()

        for fund in funds_to_update:
            fund.master_fund_id = target_data.master_fund_id

        # Commit the fund reassignments to ensure foreign key constraints are satisfied
        await sess.commit()

        # Now delete the source master (no funds reference it anymore)
        delete_master_stmt = select(FundMaster).where(
            FundMaster.id == source_data.master_fund_id,
        )
        delete_master_result = await sess.execute(delete_master_stmt)
        master_to_delete = delete_master_result.scalar_one()
        await sess.delete(master_to_delete)
        await sess.commit()

        return {
            "target_master_id": target_data.master_fund_id,
            "deleted_master_id": source_data.master_fund_id,
            "combined_balance": float(combined_balance),
            "funds_combined": len(funds_to_update),
        }


async def unlink_fund_and_split_master(
    fund_id: int,
    keep_amount: float,
    session: AsyncSession | None = None,
) -> dict:
    """
    Unlink a fund from its master and create a new master with specified balance.

    Args:
        fund_id: Fund to unlink
        keep_amount: Amount to keep with this fund's new master
        session: Optional database session

    Returns:
        Dict with new master info

    Raises:
        ValueError: If keep_amount exceeds master balance

    """
    keep_amount_decimal = Decimal(str(keep_amount))

    async with get_session(session) as sess:
        # Get fund and master
        fund_query = (
            select(Fund.id, Fund.master_fund_id, FundMaster.total_amount, Budget.name)
            .join(FundMaster, Fund.master_fund_id == FundMaster.id)
            .join(Budget, Fund.id == Budget.id)
            .where(Fund.id == fund_id)
        )
        fund_result = await sess.execute(fund_query)
        fund_data = fund_result.first()

        if not fund_data:
            msg = f"Fund {fund_id} not found"
            raise ValueError(msg)

        # Validate keep_amount
        if keep_amount_decimal > fund_data.total_amount:
            msg = (
                f"keep_amount ({keep_amount}) exceeds master balance "
                f"({fund_data.total_amount})"
            )
            raise ValueError(msg)

        # Get old master
        old_master_stmt = select(FundMaster).where(
            FundMaster.id == fund_data.master_fund_id,
        )
        old_master_result = await sess.execute(old_master_stmt)
        old_master = old_master_result.scalar_one()

        # Create new master with keep_amount
        new_master = FundMaster(
            name=fund_data.name,
            total_amount=keep_amount_decimal,
            created_at=datetime.now(UTC),
        )
        sess.add(new_master)
        await sess.flush()

        # Update old master (subtract keep_amount)
        old_master.total_amount -= keep_amount_decimal

        # Get fund and update to point to new master
        fund_stmt = select(Fund).where(Fund.id == fund_id)
        fund_result = await sess.execute(fund_stmt)
        fund = fund_result.scalar_one()
        fund.master_fund_id = new_master.id

        await sess.commit()

        return {
            "fund_id": fund_id,
            "new_master_id": new_master.id,
            "new_master_balance": float(keep_amount_decimal),
            "old_master_id": fund_data.master_fund_id,
            "old_master_balance": float(old_master.total_amount),
        }
