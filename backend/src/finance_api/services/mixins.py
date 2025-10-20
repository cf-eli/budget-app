from logging import INFO, Logger, getLogger
from typing import Any
class LoggingMixin:
    """Mixin to provide logging capabilities to classes."""
    @property
    def logger(self) -> Logger:
        """Get logger instance, creating if needed."""
        if not hasattr(self, '_logger') or self._logger is None:
            self._logger = getLogger(self.__class__.__name__)
        return self._logger

    def log(self, msg: str, *args: Any, level: int = INFO, **kwargs: Any) -> None:
        if self.logger:
            self.logger.log(level, msg, *args, **kwargs)