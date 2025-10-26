"""Service mixins."""

from logging import INFO, Logger, getLogger


class LoggingMixin:
    """Mixin to provide logging capabilities to classes."""

    @property
    def logger(self) -> Logger:
        """Get logger instance, creating if needed."""
        if not hasattr(self, "_logger") or self._logger is None:
            self._logger = getLogger(self.__class__.__name__)
        return self._logger

    def log(self, msg: str, level: int = INFO) -> None:
        """
        Log a message at the specified level.

        Args:
            msg: Message to log
            level: Logging level (default: INFO)

        """
        if self.logger:
            self.logger.log(level, msg)
