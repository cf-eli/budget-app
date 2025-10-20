from litestar import delete, post, get, Request, Router, put
from litestar import status_codes
from finance_api.crud import transaction as trans_crud
from typing import Dict
from finance_api.crud.account import save_account
from finance_api.crud.organization import save_organization
from finance_api.crud.user import ensure_user, get_all_users
from finance_api.services.simplefin import SimpleFin
from finance_api.models.db import engine
from finance_api.models.transaction import SimpleFinTransaction
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException
from finance_api.schemas.finance import CreateBreakdownRequest, CreateLineItemRequest, GetTransactionsListResponse, TransactionLineItemResponse, TransactionWithBreakdownResponse


@get(
    "/",
    response=list[SimpleFinTransaction],
    status_code=status_codes.HTTP_200_OK,
)
async def get_transactions(request: Request, page: int, descending: bool, sort_by: str, rows_per_page: int) -> GetTransactionsListResponse:  #  list[SimpleFinTransaction]:
    """Get all transactions for the authenticated user."""
    print(f"Called get_transactions with page={page}, descending={descending}, sort_by={sort_by}, rows_per_page={rows_per_page}")
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {"id": "A user"}  # For testing purposes when auth is disabled

    user = await ensure_user(request_user["id"])
    if not user:
        raise Exception("User not found")  # TODO Change to proper exception handling
    transactions = await trans_crud.get_transactions(user.id)
    transactions = GetTransactionsListResponse.model_validate(
        {"transactions": transactions}
    )
    
    return transactions#{"message": "Transactions fetched successfully", "transactions": user.accounts}

@post(
    "/update",
    response=Dict[str, str],
    tags=["Daily"],
    status_code=status_codes.HTTP_201_CREATED,
)
async def update_transactions(request: Request) -> Dict[str, str]:
    """Update transactions for all accounts of the all users.

    This endpoint fetches new transactions from the financial data provider
    for all accounts associated with all user and saves them
    to the database. It returns the number of new transactions added for each account.

    Returns:
        A dictionary mapping account IDs to the number of new transactions added.
    """
    # user = request.user
    # user: User = await ensure_user(user["id"])
    # if not user:
    #     raise Exception("User not found") # TODO Change to proper exception handling

    users = await get_all_users()
    simplefin = SimpleFin()
    for user in users:
        financial_data = await simplefin.fetch_account_data(user.access_url)

        async with engine.begin() as conn:
            for account in financial_data.accounts:
                # Save organization
                await save_organization(account.org)

                # Save account
                await save_account(account, user.id)

                # Save transactions
                await trans_crud.save_transactions(account.id, account.transactions)

                # Save holdings
                # self._save_holdings(conn, account.id, account.holdings)
    return {"message": "Transactions updated successfully"}


@post("/{transaction_id:int}/breakdown", status_code=status_codes.HTTP_201_CREATED)
async def create_breakdown(
    transaction_id: int,
    data: CreateBreakdownRequest
) -> TransactionWithBreakdownResponse:
    '''Break down a transaction into line items.'''
    line_items_data = [item.model_dump() for item in data.line_items]
    await trans_crud.create_transaction_breakdown(transaction_id, line_items_data)
    result = await trans_crud.get_transaction_with_breakdown(transaction_id)
    result = TransactionWithBreakdownResponse.model_validate(result)
    return result

@get("/{transaction_id:int}/breakdown")
async def get_breakdown(transaction_id: int) -> TransactionWithBreakdownResponse:
    '''Get transaction with breakdown.'''
    result = await trans_crud.get_transaction_with_breakdown(transaction_id)
    if not result:
        raise Exception(f"Transaction {transaction_id} not found")
    result = TransactionWithBreakdownResponse.model_validate(result)
    return result

@put("/line-items/{line_item_id:int}")
async def update_line_item_endpoint(
    line_item_id: int,
    data: CreateLineItemRequest
) -> TransactionLineItemResponse:
    '''Update a line item.'''
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
async def delete_line_item_endpoint(line_item_id: int) -> dict:
    '''Delete a line item.'''
    await trans_crud.delete_line_item(line_item_id)
    return {"message": "Line item deleted"}

transactions_router = Router(
    path="/api/v1/transactions",
    route_handlers=[get_transactions, update_transactions, create_breakdown, get_breakdown, update_line_item_endpoint, delete_line_item_endpoint],
    tags=["Transactions"],
)
