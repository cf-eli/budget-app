"""Litestar application factory and configuration."""

import logging
import traceback
from typing import Any

import jwt
from litestar import Request, Router
from litestar.app import Litestar
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import ASGIMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.response import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.types import ASGIApp, Middleware, Receive, Scope, Send

from finance_api.config import settings
from finance_api.controllers.budget import budget_router
from finance_api.controllers.health import health_router
from finance_api.controllers.transaction import transactions_router
from finance_api.controllers.user import user_router
from finance_api.crud.user import ensure_user
from finance_api.models.user import User


class JWTUserMiddleware(ASGIMiddleware):
    """Middleware for JWT authentication and user context."""

    def __init__(
        self,
        secret: str,
        jwt_algorithm: str = "HS256",
        jwt_audience: str = "test-dev",
    ) -> None:
        """
        Initialize JWT middleware.

        Args:
            secret: JWT secret key
            jwt_algorithm: JWT algorithm to use
            jwt_audience: JWT audience

        """
        self.secret = secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_audience = jwt_audience

    async def handle(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        next_app: ASGIApp,
    ) -> None:
        """Process the request and add user context."""
        if scope["type"] == "http":
            if not settings.enable_auth:
                # When auth is disabled, use default user
                scope["user"] = {"id": settings.dev_default_user_id}
            else:
                # Get headers from scope
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode()
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = jwt.decode(
                            token,
                            self.secret,
                            algorithms=[self.jwt_algorithm],
                            audience=self.jwt_audience,
                        )
                        # Attach user to scope
                        scope["user"] = {
                            "id": payload.get("sub"),
                            "name": payload.get("name"),
                            "first_name": payload.get("given_name"),
                            "last_name": payload.get("family_name"),
                            "email": payload.get("email"),
                            "roles": payload.get("roles", []),
                        }
                    except (
                        jwt.ExpiredSignatureError
                    ):  # TODO(cf-eli): #004 Change to proper exception handling
                        scope["user"] = None
                    except jwt.InvalidAudienceError:
                        scope["user"] = None
                    except jwt.PyJWTError:
                        scope["user"] = None
                else:
                    scope["user"] = None

        # Call the next middleware/handler
        await next_app(scope, receive, send)


def get_middlewares() -> list[Middleware]:
    """Get list of middlewares based on settings."""
    middlewares = []
    # if settings.enable_auth:
    middlewares.append(
        JWTUserMiddleware(
            secret=settings.homelab_client_secret,
            jwt_algorithm=settings.jwt_algorithm,
            jwt_audience=settings.finance_jwt_aud,
        ),
    )
    return middlewares


def get_openapi_config() -> OpenAPIConfig:
    """Get OpenAPI configuration for the application."""
    version = "1.0.0"

    base_config = {
        "title": "Finance API",
        "version": version,
        "description": "API for managing financial data and transactions.",
        "path": "/",
        "render_plugins": [SwaggerRenderPlugin(path="/docs"), RedocRenderPlugin()],
    }

    base_config["components"] = Components(
        security_schemes={
            "bearerAuth": SecurityScheme(
                type="http",
                scheme="bearer",
                bearer_format="JWT",
                description="Paste your JWT here",
            ),
        },
    )
    base_config["security"] = [{"bearerAuth": []}]

    return OpenAPIConfig(**base_config)


def get_cors_config() -> CORSConfig:
    """Get CORS configuration for the application."""
    return CORSConfig(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=False,
    )


async def user_dependency(request: Request) -> User | None:
    """Dependency to get the current user."""
    request_user = request.user

    if request_user is None:
        msg = "Authentication required"
        raise NotAuthorizedException(msg)

    if not request_user.get("id"):
        msg = "User ID missing in token"
        raise NotAuthorizedException(msg)
    return await ensure_user(request_user["id"])


def get_routes() -> list[Router]:
    """Get list of route handlers for the application."""
    return [
        user_router,
        budget_router,
        transactions_router,
        health_router,
    ]


logger = logging.getLogger("API.Errors")


def exception_handler(request: Request, exc: Exception) -> Response:
    """Log and handle exceptions."""
    logger.error("Exception in %s %s: %s", request.method, request.url, exc)
    logger.error(traceback.format_exc())

    status_code = getattr(exc, "status_code", HTTP_500_INTERNAL_SERVER_ERROR)
    detail = getattr(exc, "detail", "")

    return Response(
        content=detail,
        status_code=status_code,
    )


def create_app() -> Litestar:
    """
    Create and return the Litestar application instance.

    This function is used to initialize the app in the ASGI server.
    """
    exception_handlers: dict[int | type[Exception], Any] = {
        Exception: exception_handler,
    }
    return Litestar(
        route_handlers=get_routes(),
        openapi_config=get_openapi_config(),
        cors_config=get_cors_config(),
        middleware=get_middlewares(),
        exception_handlers=exception_handlers,
        dependencies={"user": Provide(user_dependency)},
    )
