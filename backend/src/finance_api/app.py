# from finance_api.controllers.controller import plaid_route
# from finance_api.controllers.budget import plaid_route as budget_route
from litestar import Router
from litestar.config.cors import CORSConfig
from litestar.middleware import AbstractMiddleware, DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import OpenAPIRenderPlugin, RedocRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.types import ASGIApp, Middleware, Receive, Scope, Send
from litestar.app import Litestar
import jwt
from finance_api.config import settings
from finance_api.controllers.user import user_router
from finance_api.controllers.budget import budget_router
from finance_api.controllers.transaction import transactions_router
class JWTUserMiddleware(AbstractMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        secret: str,
        jwt_algorithm: str = "HS256",
        jwt_audience: str = "test-dev",
    ):
        super().__init__(app)
        self.secret = secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_audience = jwt_audience

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
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
                except jwt.ExpiredSignatureError:
                    scope["user"] = None
                except jwt.InvalidAudienceError:
                    scope["user"] = None
                except jwt.PyJWTError as e:
                    scope["user"] = None
            else:
                scope["user"] = None

        # Call the next middleware/handler
        await self.app(scope, receive, send)


def get_middlewares() -> list[Middleware]:
    """Get list of middlewares based on settings."""

    middlewares = []
    if settings.enable_auth:
        middlewares.append(
            DefineMiddleware(
                JWTUserMiddleware,
                secret=settings.homelab_client_secret,
                jwt_algorithm=settings.jwt_algorithm,
                jwt_audience=settings.finance_jwt_aud,
            )
        )
    return middlewares


def get_openapi_config() -> OpenAPIConfig:
    version = "1.0.0"
    
    base_config = {
        "title": "Finance API",
        "version": version,
        "description": "API for managing financial data and transactions.",
        "path": "/",
        "render_plugins": [SwaggerRenderPlugin(path="/docs"), RedocRenderPlugin()],
    }
    
    # if settings.enable_auth: # TODO: controllers should have a wrapper that get user model or return fake if auth is disabled
    base_config["components"] = Components(
        security_schemes={
            "bearerAuth": SecurityScheme(
                type="http",
                scheme="bearer",
                bearer_format="JWT",
                description="Paste your JWT here",
            )
        }
    )
    base_config["security"] = [{"bearerAuth": []}]
    
    return OpenAPIConfig(**base_config)


def get_cors_config() -> CORSConfig:
    return CORSConfig(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=False,
    )


def get_routes() -> list[Router]:
    return [
        user_router,
        budget_router,
        transactions_router,
    ]

import logging
import traceback
from litestar.response import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar import Request
from typing import Any
logger = logging.getLogger("API.Errors")

def exception_handler(request: Request, exc: Exception) -> Response:
    """Log and handle exceptions."""
    logger.error(f"Exception in {request.method} {request.url}: {exc}")
    logger.error(traceback.format_exc())
    
    return Response(
        content={"detail": str(exc), "type": type(exc).__name__},
        status_code=HTTP_500_INTERNAL_SERVER_ERROR
    )


def create_app() -> Litestar:
    """
    Create and return the Litestar application instance.
    This function is used to initialize the app in the ASGI server.
    """
    exception_handlers: dict[int | type[Exception], Any] = {
        Exception: exception_handler
    }
    app = Litestar(
        route_handlers=get_routes(),
        openapi_config=get_openapi_config(),
        cors_config=get_cors_config(),
        middleware=get_middlewares(),
        exception_handlers=exception_handlers,
    )
    return app
