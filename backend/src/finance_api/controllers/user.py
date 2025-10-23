from litestar import Router, post, get, Request, put
from litestar import status_codes
from finance_api.crud.transaction import save_transactions
from typing import Dict
from finance_api.crud.account import save_account
from finance_api.crud.organization import save_organization
from finance_api.crud.user import ensure_user, get_all_users
from finance_api.services.simplefin import SimpleFin
from finance_api.models.db import engine
from finance_api.crud.user import update_access_url
from finance_api.models.user import User
from finance_api.schemas.schema import TokenRequest
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException

@put(f"/token", response=Dict[str, str], status_code=status_codes.HTTP_200_OK)
async def update_access_url_endpoint(request: Request, data: TokenRequest) -> Dict[str, str]:
    """Update the access URL for the authenticated user.

    This endpoint allows the authenticated user to update their access URL,
    which is used to fetch financial data from the external provider.

    Request Body:
        {
            "token": "new_token_string"
        }

    Returns:
        A dictionary confirming the update of the access URL.
    """
    try:
        request_user = request.user
    except ImproperlyConfiguredException:
        request_user = {"id": "adb59b2f-826e-4b0a-82e5-09d69ba0e615"}  # For testing purposes when auth is disabled
    print("here2")
    user: User = await ensure_user(request_user["id"])
    if not user:
        raise Exception("User not found")  # TODO Change to proper exception handling

    data_dict = data.model_dump()
    setup_token = data_dict.get("token")
    if not setup_token:
        raise Exception("Token is required")  # TODO Change to proper exception handling
    print(user)
    simplefin = SimpleFin()
    claim_url = await simplefin.claim_setup_token(setup_token)  # Validate the token by attempting to claim the access URL
    await update_access_url(user.auth_user_id, claim_url)
    return {"message": "Access URL updated successfully"}

user_router = Router(
    path="/api/v1/user", route_handlers=[update_access_url_endpoint], tags=["User"]
)

# @post(f"{transaction_route}/transactions/update", response=Dict[str, str], tags=["Transactions, Daily"], status_code=status_codes.HTTP_201_CREATED)
# async def update_transactions(request: Request):
#     """Update transactions for all accounts of the all users.
    
#     This endpoint fetches new transactions from the financial data provider
#     for all accounts associated with all user and saves them
#     to the database. It returns the number of new transactions added for each account.
    
#     Returns:
#         A dictionary mapping account IDs to the number of new transactions added.
#     """
#     # user = request.user
#     # user: User = await ensure_user(user["id"])
#     # if not user:
#     #     raise Exception("User not found") # TODO Change to proper exception handling

#     users = await get_all_users()
#     total_new_transactions = 0
#     account_transaction_counts = {}
#     simplefin = SimpleFin()
#     for user in users:
#         financial_data = await simplefin.fetch_account_data(user.access_url)

#         async with engine.begin() as conn:
#             for account in financial_data.accounts:
#                 # Save organization
#                 await save_organization(account.org)
                
#                 # Save account
#                 await save_account(account)
                
#                 # Save transactions
#                 await save_transactions(account.id, account.transactions)
                
#                 # Save holdings
#                 # self._save_holdings(conn, account.id, account.holdings)
#     return {"message": "Transactions updated successfully"}

        