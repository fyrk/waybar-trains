from abc import ABC, abstractmethod
from typing import Any

from .types import Status


class BaseProvider(ABC):
    def __init__(self):
        super().__init__()

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

    def get_status(self) -> Status | None:
        """
        tries to fetch provider data, and if successful returns a status string, else None
        """
        if not self._is_connected():
            return None
        return self._get_status_from_data(self._fetch_data())
