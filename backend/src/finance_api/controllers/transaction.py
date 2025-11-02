"""Transaction management endpoints."""

from litestar import Router, delete, get, patch, post, put, status_codes

from finance_api.crud import transaction as trans_crud
from finance_api.crud.account import save_account
from finance_api.crud.organization import save_organization
from finance_api.crud.user import get_all_users
from finance_api.models.db import engine
from finance_api.models.user import User
from finance_api.schemas.exceptions import FinanceServerError
from finance_api.schemas.finance import (
    CreateBreakdownRequest,
    CreateLineItemRequest,
    TransactionLineItemResponse,
    TransactionWithBreakdownResponse,
)
from finance_api.schemas.schema import MessageResponse
from finance_api.schemas.transactions import (
    MarkTransactionTypeRequest,
    PaginatedTransactionResponse,
    TransactionResponse,
)
from finance_api.services.simplefin import SimpleFin


@get(
    "/",
    response=PaginatedTransactionResponse,
    status_code=status_codes.HTTP_200_OK,
)
async def get_transactions(
    user: User,
    page: int = 1,
    descending: bool = True,
    sort_by: str = "transacted_at",  # noqa: ARG001
    rows_per_page: int = 10,
    include_excluded: bool = False,
    transaction_type: str | None = None,  # noqa: ARG001
    month: int | None = None,
    year: int | None = None,
) -> PaginatedTransactionResponse:
    """
    Get transactions with optional filtering.

    Args:
        user: The authenticated user
        page: Page number for pagination (1-indexed)
        descending: Sort order (True for descending, False for ascending)
        sort_by: Field to sort by
        rows_per_page: Number of rows per page
        include_excluded: Whether to include excluded transactions
        transaction_type: Optional filter by transaction type
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        Paginated response with transactions and total count

    """
    # Calculate offset from page number (convert from 1-indexed to 0-indexed)
    offset = (page - 1) * rows_per_page

    # TODO(cf-eli): #004 Change to proper exception handling
    transactions, total = await trans_crud.get_transactions_paginated(
        user.id,
        month=month,
        year=year,
        include_excluded=include_excluded,
        sort_desc=descending,
        limit=rows_per_page,
        offset=offset,
    )

    return PaginatedTransactionResponse(
        transactions=[TransactionResponse.model_validate(txn) for txn in transactions],
        total=total,
        page=page,
        rows_per_page=rows_per_page,
    )


@post(
    "/update",
    response=dict[str, str],
    tags=["Daily"],
    status_code=status_codes.HTTP_201_CREATED,
)
async def update_transactions() -> MessageResponse:
    """
    Update transactions for all accounts of the all users.

    This endpoint fetches new transactions from the financial data provider
    for all accounts associated with all user and saves them
    to the database. It returns the number of new transactions added for each account.

    Returns:
        A dictionary mapping account IDs to the number of new transactions added.

    """
    users = await get_all_users()
    simplefin = SimpleFin()
    for user in users:
        financial_data = await simplefin.fetch_account_data(user.access_url)

        async with engine.begin():
            for account in financial_data.accounts:
                # Save organization
                await save_organization(account.org)

                # Save account
                await save_account(account, user.id)

                # Save transactions
                await trans_crud.save_transactions(account.id, account.transactions)
    return MessageResponse(message="Transactions updated successfully")


@post("/{transaction_id:int}/breakdown", status_code=status_codes.HTTP_201_CREATED)
async def create_breakdown(
    transaction_id: int,
    data: CreateBreakdownRequest,
) -> TransactionWithBreakdownResponse:
    """Break down a transaction into line items."""
    line_items_data = [item.model_dump() for item in data.line_items]
    await trans_crud.create_transaction_breakdown(transaction_id, line_items_data)
    result = await trans_crud.get_transaction_with_breakdown(transaction_id)
    return TransactionWithBreakdownResponse.model_validate(result)


@get("/{transaction_id:int}/breakdown")
async def get_breakdown(transaction_id: int) -> TransactionWithBreakdownResponse:
    """Get transaction with breakdown."""
    result = await trans_crud.get_transaction_with_breakdown(transaction_id)
    if not result:
        msg = f"Transaction {transaction_id} not found"
        raise FinanceServerError(msg)
    return TransactionWithBreakdownResponse.model_validate(result)


@put("/line-items/{line_item_id:int}")
async def update_line_item_endpoint(
    line_item_id: int,
    data: CreateLineItemRequest,
) -> TransactionLineItemResponse:
    """Update a line item."""
    item = await trans_crud.update_line_item(
        line_item_id,
        description=data.description,
        amount=data.amount,
        quantity=data.quantity,
        unit_price=data.unit_price,
        category=data.category,
        budget_id=data.budget_id,
        notes=data.notes,
    )
    return TransactionLineItemResponse.model_validate(item)


@delete("/line-items/{line_item_id:int}", status_code=status_codes.HTTP_200_OK)
async def delete_line_item_endpoint(line_item_id: int) -> MessageResponse:
    """Delete a line item."""
    await trans_crud.delete_line_item(line_item_id)
    return MessageResponse(message="Line item deleted")


@patch("{transaction_id:int}/type", status_code=status_codes.HTTP_200_OK)
async def mark_transaction_type_endpoint(
    transaction_id: int,
    data: MarkTransactionTypeRequest,
) -> TransactionResponse:
    """Mark a transaction as transfer, payment, etc."""
    transaction = await trans_crud.mark_transaction_type(
        transaction_id,
        transaction_type=data.transaction_type.value if data.transaction_type else None,
        exclude_from_budget=data.exclude_from_budget,
    )
    return TransactionResponse.model_validate(transaction)


transactions_router = Router(
    path="/api/v1/transactions",
    route_handlers=[
        get_transactions,
        update_transactions,
        create_breakdown,
        get_breakdown,
        update_line_item_endpoint,
        delete_line_item_endpoint,
        mark_transaction_type_endpoint,
    ],
    tags=["Transactions"],
)
