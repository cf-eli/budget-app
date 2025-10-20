# import sqlalchemy core
from finance_api.models.transaction import SimpleFinTransaction, TransactionLineItem
from sqlalchemy import select, insert, func
from finance_api.models.budget import (
    # BudgetType,
    Income,
    Expense,
    # Flexible,
    Fund,
)
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from finance_api.models.budget import (
    Budget,
    Income,
    Expense,
    # Flexible,
    Fund,
    # BudgetType,
)
from finance_api.models.db import engine
from datetime import datetime


async def create_budget(user_id: int, name: str) -> int:
    """Creates a budget entry and returns the budget ID."""
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    async with AsyncSession(engine) as session:
        stmt = (
            insert(Budget)
            .values(user_id=user_id, name=name, month=current_month, year=current_year)
            .returning(Budget.id)
        )
        result = await session.execute(stmt)
        await session.commit()
        budget_id = result.scalar_one()
        return budget_id


async def create_income(
    user_id: int,
    name: str,
    fixed: bool,
    expected_amount: float | None,
    min_amount: float | None,
    max_amount: float | None,
) -> None:
    """Creates a budget with income details."""
    # Create budget first
    budget_id = await create_budget(user_id, name)

    # Create income entry linked to budget
    async with AsyncSession(engine) as session:
        stmt = insert(Income).values(
            id=budget_id,
            fixed=fixed,
            expected_amount=expected_amount,
            min=min_amount,
            max=max_amount,
        )
        await session.execute(stmt)
        await session.commit()


async def create_expense(
    user_id: int,
    name: str,
    fixed: bool,
    flexible: bool,
    expected_amount: float | None,
    min_amount: float | None,
    max_amount: float | None,
) -> None:
    """Creates a budget with expense details."""
    budget_id = await create_budget(user_id, name)

    async with AsyncSession(engine) as session:
        stmt = insert(Expense).values(
            id=budget_id,
            fixed=fixed,
            flexible=flexible,
            expected_amount=expected_amount,
            min=min_amount,
            max=max_amount,
        )
        await session.execute(stmt)
        await session.commit()


async def create_fund(
    user_id: int,
    name: str,
    priority: int | None,
    increment: float | None,
    current_amount: float = 0.0,
    max_amount: float | None = None,
) -> None:
    """Creates a budget with fund details."""
    budget_id = await create_budget(user_id, name)

    async with AsyncSession(engine) as session:
        stmt = insert(Fund).values(
            id=budget_id,
            priority=priority,
            increment=increment,
            current_amount=current_amount,
            max=max_amount,
        )
        await session.execute(stmt)
        await session.commit()


async def get_budgets(user_id: int) -> dict:
    """Get all budgets for a user with transaction sums (accounting for line items)."""
    income_alias = aliased(Income)
    expense_alias = aliased(Expense)
    fund_alias = aliased(Fund)

    # Get all budget sums at once (optimized, includes line items)
    budget_sums = await get_all_budget_sums_with_line_items()

    query = (
        select(
            Budget.id.label("budget_id"),
            Budget.user_id,
            Budget.name,
            Budget.enable,
            Budget.deleted,
            income_alias.id.label("income_id"),
            income_alias.fixed.label("income_fixed"),
            income_alias.expected_amount.label("income_expected_amount"),
            income_alias.min.label("income_min"),
            income_alias.max.label("income_max"),
            expense_alias.id.label("expense_id"),
            expense_alias.flexible.label("expense_flexible"),
            expense_alias.fixed.label("expense_fixed"),
            expense_alias.expected_amount.label("expense_expected_amount"),
            expense_alias.min.label("expense_min"),
            expense_alias.max.label("expense_max"),
            fund_alias.id.label("fund_id"),
            fund_alias.priority.label("fund_priority"),
            fund_alias.increment.label("fund_increment"),
            fund_alias.current_amount.label("fund_current_amount"),
            fund_alias.max.label("fund_max"),
        )
        .where(Budget.user_id == user_id)
        .outerjoin(income_alias, Budget.id == income_alias.id)
        .outerjoin(expense_alias, Budget.id == expense_alias.id)
        .outerjoin(fund_alias, Budget.id == fund_alias.id)
    )

    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        rows = result.all()

    incomes = []
    expenses = []
    flexibles = []
    funds = []

    for row in rows:
        row_dict = row._mapping
        budget_id = row_dict["budget_id"]
        transaction_sum = budget_sums.get(budget_id, 0.0)

        budget_info = {
            "id": budget_id,
            "user_id": row_dict["user_id"],
            "name": row_dict["name"],
            "enable": row_dict["enable"],
            "deleted": row_dict["deleted"],
            "transaction_sum": float(transaction_sum),
        }

        if row_dict["income_id"] is not None:
            incomes.append(
                {
                    **budget_info,
                    "fixed": row_dict["income_fixed"],
                    "expected_amount": row_dict["income_expected_amount"],
                    "min": row_dict["income_min"],
                    "max": row_dict["income_max"],
                    "amount_after_transactions": row_dict["income_expected_amount"] + transaction_sum,
                }
            )
        elif row_dict["expense_id"] is not None:
            expense_data = {
                **budget_info,
                "fixed": row_dict["expense_fixed"],
                "expected_amount": row_dict["expense_expected_amount"],
                "min": row_dict["expense_min"],
                "max": row_dict["expense_max"],
                # For expenses, transaction_sum is negative, so subtract from expected
                "amount_after_transactions": row_dict["expense_expected_amount"] + transaction_sum,
            }
            if row_dict["expense_flexible"]:
                flexibles.append(expense_data)
            else:
                expenses.append(expense_data)
        elif row_dict["fund_id"] is not None:
            funds.append(
                {
                    **budget_info,
                    "priority": row_dict["fund_priority"],
                    "increment": row_dict["fund_increment"],
                    "current_amount": row_dict["fund_current_amount"],
                    "max": row_dict["fund_max"],
                    "amount_after_transactions": row_dict["fund_current_amount"] + transaction_sum,
                }
            )

    return {
        "incomes": incomes,
        "expenses": expenses,
        "flexibles": flexibles,
        "funds": funds,
    }




async def get_income_sum(user_id: int) -> float:
    """Get total income for a user."""
    query = (
        select(func.sum(SimpleFinTransaction.amount))
        .select_from(Budget)
        .join(Income, Budget.id == Income.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(SimpleFinTransaction.amount > 0)
    )
    
    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        return result.scalar() or 0.0

async def get_expense_sum(user_id: int) -> float:
    """Get total fixed expenses for a user."""
    query = (
        select(func.sum(func.abs(SimpleFinTransaction.amount)))
        .select_from(Budget)
        .join(Expense, Budget.id == Expense.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(Expense.flexible == False)
        .where(SimpleFinTransaction.amount < 0)
    )
    
    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        return result.scalar() or 0.0

async def get_flexible_sum(user_id: int) -> float:
    """Get total flexible expenses for a user."""
    query = (
        select(func.sum(func.abs(SimpleFinTransaction.amount)))
        .select_from(Budget)
        .join(Expense, Budget.id == Expense.id)
        .join(SimpleFinTransaction, SimpleFinTransaction.budget_id == Budget.id)
        .where(Budget.user_id == user_id)
        .where(Expense.flexible == True)
        .where(SimpleFinTransaction.amount < 0)
    )
    
    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        return result.scalar() or 0.0

async def get_fund_sum(user_id: int) -> float:
    """Get total funds allocated for a user."""
    query = (
        select(func.sum(Fund.current_amount))
        .select_from(Budget)
        .join(Fund, Budget.id == Fund.id)
        .where(Budget.user_id == user_id)
    )
    
    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        return result.scalar() or 0.0
    
async def get_budgets_name() -> list[dict]:
    """Get all budget IDs and names."""
    query = select(Budget.id, Budget.name)
    
    async with AsyncSession(engine) as session:
        result = await session.execute(query)
        return [dict(row._mapping) for row in result.all()]


async def get_budget_sum_with_line_items(budget_id: int) -> float:
    """
    Get budget sum including line items.
    If a transaction is split, use line items; otherwise use parent transaction.
    """
    async with AsyncSession(engine) as session:
        # Sum from transactions that aren't split
        unsplit_query = (
            select(func.sum(SimpleFinTransaction.amount))
            .where(SimpleFinTransaction.budget_id == budget_id)
            .where(SimpleFinTransaction.is_split == False)
        )
        unsplit_result = await session.execute(unsplit_query)
        unsplit_sum = unsplit_result.scalar() or 0.0
        
        # Sum from line items where parent is split
        split_query = (
            select(func.sum(TransactionLineItem.amount))
            .where(TransactionLineItem.budget_id == budget_id)
        )
        split_result = await session.execute(split_query)
        split_sum = split_result.scalar() or 0.0
        
        return unsplit_sum + split_sum

async def get_all_budget_sums_with_line_items() -> dict[int, float]:
    """
    Get all budget sums at once (optimized for get_budgets query).
    Returns dict of {budget_id: total_amount}
    """
    async with AsyncSession(engine) as session:
        # Sum unsplit transactions grouped by budget
        unsplit_query = (
            select(
                SimpleFinTransaction.budget_id,
                func.sum(SimpleFinTransaction.amount).label("total")
            )
            .where(SimpleFinTransaction.budget_id.isnot(None))
            .where(SimpleFinTransaction.is_split == False)
            .group_by(SimpleFinTransaction.budget_id)
        )
        unsplit_result = await session.execute(unsplit_query)
        unsplit_sums = {row.budget_id: row.total for row in unsplit_result}
        
        # Sum line items grouped by budget
        split_query = (
            select(
                TransactionLineItem.budget_id,
                func.sum(TransactionLineItem.amount).label("total")
            )
            .where(TransactionLineItem.budget_id.isnot(None))
            .group_by(TransactionLineItem.budget_id)
        )
        split_result = await session.execute(split_query)
        split_sums = {row.budget_id: row.total for row in split_result}
        
        # Combine both
        all_budget_ids = set(unsplit_sums.keys()) | set(split_sums.keys())
        combined = {}
        for budget_id in all_budget_ids:
            combined[budget_id] = (
                unsplit_sums.get(budget_id, 0.0) + 
                split_sums.get(budget_id, 0.0)
            )
        
        return combined