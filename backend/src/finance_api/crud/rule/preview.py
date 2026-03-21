"""Rule preview logic for dry-run rule matching."""

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from finance_api.crud.rule.application import (
    _get_resolved_budget_for_rule,
    _get_transactions_for_rules,
    _resolve_budgets_for_rules,
    _should_process_transaction,
)
from finance_api.crud.rule.base import get_rules
from finance_api.crud.rule.matching import matches_all_conditions
from finance_api.models.budget import Budget
from finance_api.models.db import get_session
from finance_api.models.transaction import SimpleFinTransaction
from finance_api.schemas.rules import (
    RulePreviewItem,
    RulePreviewResponse,
)

if TYPE_CHECKING:
    from finance_api.models.transaction_rule import TransactionRule


def _build_preview_item(
    transaction: SimpleFinTransaction,
    rule: "TransactionRule",
    resolved_budget: Budget | None = None,
) -> RulePreviewItem:
    """Build a RulePreviewItem from a transaction and matching rule."""
    # Use resolved budget for the target month, fall back to rule's target
    if resolved_budget:
        target_id = resolved_budget.id
        target_name = resolved_budget.name
    else:
        target_id = rule.target_budget_id
        target_name = rule.target_budget.name if rule.target_budget else None

    return RulePreviewItem(
        transaction_id=transaction.id,
        transaction_description=transaction.description or "",
        transaction_payee=transaction.payee,
        transaction_amount=transaction.amount,
        transacted_at=transaction.transacted_at,
        account_name=transaction.account.name if transaction.account else "",
        org_name=(
            transaction.account.org.name
            if transaction.account and transaction.account.org
            else None
        ),
        rule_name=rule.name,
        rule_id=rule.id,
        target_budget_id=target_id,
        target_budget_name=target_name,
        current_budget_id=transaction.budget_id,
        current_budget_name=transaction.budget.name if transaction.budget else None,
        target_transaction_type=rule.target_transaction_type,
        target_exclude_from_budget=rule.target_exclude_from_budget,
        selected=True,
    )


async def preview_rule_application(
    user_id: int,
    month: int,
    year: int,
    override_existing: bool = False,
    session: AsyncSession | None = None,
) -> RulePreviewResponse:
    """
    Preview which transactions would be assigned to budgets.

    Returns a list of matches without making any changes.
    Rules are resolved to the correct budget for the target month/year.
    """
    async with get_session(session) as sess:
        rules = await get_rules(user_id, include_inactive=False, session=sess)
        if not rules:
            return RulePreviewResponse(
                assignments=[],
                total_count=0,
                already_assigned_count=0,
                new_assignment_count=0,
            )

        resolved_budgets = await _resolve_budgets_for_rules(
            user_id,
            rules,
            month,
            year,
            sess,
        )

        transactions = await _get_transactions_for_rules(
            user_id,
            month,
            year,
            include_pending=False,
            session=sess,
        )

        assignments: list[RulePreviewItem] = []
        already_assigned_count = 0
        new_assignment_count = 0
        matched_transaction_ids: set[int] = set()

        for rule in rules:
            resolved_budget = _get_resolved_budget_for_rule(rule, resolved_budgets)
            # Skip if rule needs a budget but none was resolved
            has_budget_action = rule.target_budget_id is not None
            has_type_action = rule.target_transaction_type is not None
            if has_budget_action and not resolved_budget:
                continue
            if not has_budget_action and not has_type_action:
                continue

            for transaction in transactions:
                if not _should_process_transaction(
                    transaction,
                    rule,
                    matched_transaction_ids,
                    override_existing,
                ):
                    continue
                if not matches_all_conditions(transaction, rule.conditions):
                    continue

                matched_transaction_ids.add(transaction.id)

                if transaction.budget_id is not None:
                    already_assigned_count += 1
                else:
                    new_assignment_count += 1

                assignments.append(
                    _build_preview_item(transaction, rule, resolved_budget),
                )

        return RulePreviewResponse(
            assignments=assignments,
            total_count=len(assignments),
            already_assigned_count=already_assigned_count,
            new_assignment_count=new_assignment_count,
        )
