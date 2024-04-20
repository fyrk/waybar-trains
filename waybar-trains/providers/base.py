from abc import ABC, abstractmethod
from logging import Logger, LoggerAdapter
from pprint import pformat
from typing import Any

from .types import Status


class ProviderLoggingAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        name = self.extra["name"]  # type:ignore[reportOptionalSubscript]
        return "[%s] %s" % (name, msg), kwargs


class BaseProvider(ABC):
    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = ProviderLoggingAdapter(logger, {"name": self.name})

    @property
    @abstractmethod
    def name(self) -> str: ...

    def _is_connected(self) -> bool:
        """heuristic to check if connected to WiFi"""
        return True

    @abstractmethod
    def _fetch_data(self) -> Any: ...

    @abstractmethod
    def _get_status_from_data(self, data: Any) -> Status | None: ...

    def get_status(self, conn_check=True) -> Status | None:
        """
        tries to fetch provider data, and if successful returns a status string, else None
        """
        try:
            self.logger.info(f"Getting status")
            if conn_check and not self._is_connected():
                self.logger.debug("Skipping, not connected to WiFi")
                return None
            data = self._fetch_data()
            self.logger.debug(f"Got data {pformat(data)}")
            return self._get_status_from_data(data)
        except:
            self.logger.exception(f"Unhandled exception while retrieving status")
