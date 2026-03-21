"""Base CRUD operations for transaction rules."""

from sqlalchemy import delete as sql_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from finance_api.models.db import get_session
from finance_api.models.transaction_rule import TransactionRule
from finance_api.schemas.rules import CreateRuleRequest, UpdateRuleRequest


async def create_rule(
    user_id: int,
    data: CreateRuleRequest,
    session: AsyncSession | None = None,
) -> TransactionRule:
    """Create a new transaction rule."""
    async with get_session(session) as sess:
        # Convert conditions to list of dicts for JSON storage
        conditions_json = [cond.model_dump() for cond in data.conditions]

        rule = TransactionRule(
            user_id=user_id,
            name=data.name,
            target_budget_id=data.target_budget_id,
            conditions=conditions_json,
            priority=data.priority,
            is_active=data.is_active,
            target_transaction_type=data.target_transaction_type,
            target_exclude_from_budget=data.target_exclude_from_budget,
        )
        sess.add(rule)
        await sess.commit()
        await sess.refresh(rule)

        # Load the target_budget relationship
        stmt = (
            select(TransactionRule)
            .where(TransactionRule.id == rule.id)
            .options(selectinload(TransactionRule.target_budget))
        )
        result = await sess.execute(stmt)
        return result.scalar_one()


async def get_rule(
    rule_id: int,
    user_id: int,
    session: AsyncSession | None = None,
) -> TransactionRule | None:
    """Get a rule by ID for a specific user."""
    async with get_session(session) as sess:
        stmt = (
            select(TransactionRule)
            .where(TransactionRule.id == rule_id, TransactionRule.user_id == user_id)
            .options(selectinload(TransactionRule.target_budget))
        )
        result = await sess.execute(stmt)
        return result.scalar_one_or_none()


async def get_rules(
    user_id: int,
    include_inactive: bool = False,
    session: AsyncSession | None = None,
) -> list[TransactionRule]:
    """Get all rules for a user, ordered by priority."""
    async with get_session(session) as sess:
        stmt = (
            select(TransactionRule)
            .where(TransactionRule.user_id == user_id)
            .options(selectinload(TransactionRule.target_budget))
            .order_by(TransactionRule.priority)
        )
        if not include_inactive:
            stmt = stmt.where(TransactionRule.is_active.is_(True))
        result = await sess.execute(stmt)
        return list(result.scalars().all())


async def update_rule(
    rule_id: int,
    user_id: int,
    data: UpdateRuleRequest,
    session: AsyncSession | None = None,
) -> TransactionRule | None:
    """Update a rule."""
    async with get_session(session) as sess:
        # Build update values from non-None fields
        update_values = {}
        if data.name is not None:
            update_values["name"] = data.name
        if data.target_budget_id is not None:
            update_values["target_budget_id"] = data.target_budget_id
        if data.conditions is not None:
            update_values["conditions"] = [
                cond.model_dump() for cond in data.conditions
            ]
        if data.priority is not None:
            update_values["priority"] = data.priority
        if data.is_active is not None:
            update_values["is_active"] = data.is_active
        if data.target_transaction_type is not None:
            update_values["target_transaction_type"] = (
                data.target_transaction_type or None
            )
        if data.target_exclude_from_budget is not None:
            update_values["target_exclude_from_budget"] = (
                data.target_exclude_from_budget
            )

        if update_values:
            await sess.execute(
                update(TransactionRule)
                .where(
                    TransactionRule.id == rule_id,
                    TransactionRule.user_id == user_id,
                )
                .values(**update_values),
            )
            await sess.commit()

        return await get_rule(rule_id, user_id, sess)


async def delete_rule(
    rule_id: int,
    user_id: int,
    session: AsyncSession | None = None,
) -> bool:
    """Delete a rule. Returns True if deleted, False if not found."""
    async with get_session(session) as sess:
        result = await sess.execute(
            sql_delete(TransactionRule).where(
                TransactionRule.id == rule_id,
                TransactionRule.user_id == user_id,
            ),
        )
        await sess.commit()
        return result.rowcount > 0


async def reorder_rules(
    user_id: int,
    rule_ids: list[int],
    session: AsyncSession | None = None,
) -> bool:
    """
    Reorder rules by setting priorities based on position in list.

    First ID in list gets priority 0, second gets 1, etc.
    """
    async with get_session(session) as sess:
        for priority, rule_id in enumerate(rule_ids):
            await sess.execute(
                update(TransactionRule)
                .where(
                    TransactionRule.id == rule_id,
                    TransactionRule.user_id == user_id,
                )
                .values(priority=priority),
            )
        await sess.commit()
        return True
