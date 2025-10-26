"""Health check endpoints."""

from litestar import Router, get, status_codes

from finance_api.schemas.schema import HealthResponse


@get("/", response=HealthResponse, status_code=status_codes.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    This endpoint returns the health status of the API.
    It can be used to verify that the service is running.

    Returns:
        A HealthResponse indicating the service is operational.

    """
    return HealthResponse(status="Ok")


health_router = Router(
    path="/api/v1/health",
    route_handlers=[health_check],
    tags=["Health"],
)
