"""ASGI entry point for the finance API application."""

from finance_api.app import create_app

app = create_app()
