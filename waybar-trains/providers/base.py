import dataclasses
import datetime
import json
import os.path
from abc import ABC, abstractmethod
from logging import LoggerAdapter, getLogger
from pprint import pformat
from typing import Any, NamedTuple

from .types import Status
from .utils import estimate_next_stop

_logger = getLogger("waybar-trains")


class BaseProvider(ABC):
    NAME: str = NotImplemented

    def __init__(self):
        super().__init__()
        self.logger = ProviderLoggingAdapter(_logger, {"name": self.NAME})

    def _is_connected(self) -> bool:
        """heuristic to check if connected to WiFi"""
        return True

    def _read_dummy_data(self, filepath):
        with open(
            os.path.join(os.path.dirname(__file__), "_dummy_data", filepath)
        ) as f:
            return json.load(f)

    @abstractmethod
    def _fetch_data(self) -> Any: ...

    @abstractmethod
    def _get_dummy_data(self) -> "DummyProviderData": ...

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
            status = self._get_status_from_data(data)
            if status is not None and not status.next_stop and status.stops:
                status = dataclasses.replace(
                    status,
                    next_stop=estimate_next_stop(status.stops),
                )
            return status
        except:
            self.logger.exception(f"Unhandled exception while retrieving status")

    def get_dummy_status(self) -> Status | None:
        data, time = self._get_dummy_data()
        self.logger.debug(f"Using dummy data from {time}")
        status = self._get_status_from_data(data)
        if status is not None and not status.next_stop and status.stops:
            status = dataclasses.replace(
                status,
                next_stop=estimate_next_stop(status.stops, time),
            )
        return status


class DummyProviderData[T](NamedTuple):
    data: T
    time: datetime.datetime


class ProviderLoggingAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        name = self.extra["name"]  # type:ignore[reportOptionalSubscript]
        return "[%s] %s" % (name, msg), kwargs
