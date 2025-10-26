"""Transaction management endpoints."""

from litestar import Request, Router, delete, get, patch, post, put, status_codes
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException

from finance_api.config import settings
from finance_api.crud import transaction as trans_crud
from finance_api.crud.account import save_account
from finance_api.crud.organization import save_organization
from finance_api.crud.user import ensure_user, get_all_users
from finance_api.models.db import engine
from finance_api.models.transaction import SimpleFinTransaction
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
    TransactionResponse,
)
from finance_api.services.simplefin import SimpleFin


@get(
    "/",
    response=list[SimpleFinTransaction],
    status_code=status_codes.HTTP_200_OK,
)
async def get_transactions(
    request: Request,
    page: int,  # noqa: ARG001
    descending: bool,  # noqa: ARG001
    sort_by: str,  # noqa: ARG001
    rows_per_page: int,  # noqa: ARG001
    include_excluded: bool = False,  # noqa: ARG001
    transaction_type: str | None = None,  # noqa: ARG001
    month: int | None = None,
    year: int | None = None,
) -> list[TransactionResponse]:
    """
    Get transactions with optional filtering.

    Args:
        request: The HTTP request object
        page: Page number for pagination
        descending: Sort order (True for descending, False for ascending)
        sort_by: Field to sort by
        rows_per_page: Number of rows per page
        include_excluded: Whether to include excluded transactions
        transaction_type: Optional filter by transaction type
        month: Optional month filter (1-12). If not provided, uses current month
        year: Optional year filter (e.g., 2024). If not provided, uses current year

    Returns:
        A list of transactions matching the criteria

    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        # Use configured default user for testing when auth is disabled
        request_user = {"id": settings.dev_default_user_id}

    user = await ensure_user(request_user["id"])
    if not user:
        msg = "User not found"
        raise FinanceServerError(msg)
    # TODO(cf-eli): #004 Change to proper exception handling
    transactions = await trans_crud.get_transactions(user.id, month=month, year=year)
    return [TransactionResponse.model_validate(txn) for txn in transactions]


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
