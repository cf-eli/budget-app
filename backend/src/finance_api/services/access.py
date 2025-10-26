"""Access control services."""

from functools import lru_cache

from finance_api.config import Settings, get_settings


@lru_cache(maxsize=1)
def get_access_settings() -> Settings:
    """Get settings singleton."""
    return get_settings()
