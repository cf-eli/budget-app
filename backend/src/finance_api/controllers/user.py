"""User management endpoints."""

from litestar import Request, Router, put, status_codes
from litestar.exceptions.http_exceptions import ImproperlyConfiguredException

from finance_api.config import settings
from finance_api.crud.user import ensure_user, update_access_url
from finance_api.schemas.exceptions import FinanceServerError
from finance_api.schemas.schema import MessageResponse, TokenRequest
from finance_api.services.simplefin import SimpleFin


@put("/token", response=MessageResponse, status_code=status_codes.HTTP_200_OK)
async def update_access_url_endpoint(
    request: Request,
    data: TokenRequest,
) -> MessageResponse:
    """
    Update the access URL for the authenticated user.

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
        # Use configured default user for testing when auth is disabled
        request_user = {"id": settings.dev_default_user_id}
    user = await ensure_user(request_user["id"])
    if not user:
        msg = "User not found"
        raise FinanceServerError(msg)  # TODO(cf-eli): #004 Change to proper exception

    data_dict = data.model_dump()
    setup_token = data_dict.get("token")
    if not setup_token:
        msg = "Token is required"
        raise FinanceServerError(msg)  # TODO(cf-eli): #004 Change to proper exception
    simplefin = SimpleFin()
    claim_url = await simplefin.claim_setup_token(
        setup_token,
    )  # Validate the token by attempting to claim the access URL
    await update_access_url(user.auth_user_id, claim_url)
    return MessageResponse(message="Access URL updated successfully")


user_router = Router(
    path="/api/v1/user",
    route_handlers=[update_access_url_endpoint],
    tags=["User"],
)
