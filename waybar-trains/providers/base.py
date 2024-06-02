import dataclasses
import datetime
import json
import os.path
from abc import ABC, abstractmethod
from logging import LoggerAdapter, getLogger
from pprint import pformat
from types import NotImplementedType
from typing import Any, Literal, NamedTuple

import requests

from .types import Status
from .utils import estimate_next_stop

_logger = getLogger("waybar-trains")


class BaseProvider(ABC):
    NAME: str = NotImplemented

    def __init__(self, session: requests.Session | None = None):
        super().__init__()
        if session is None:
            session = requests.Session()
        self._session = session
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

    def attempt_login(
        self,
    ) -> (
        Literal["success"]
        | Literal["already_logged_in"]
        | Literal["error"]
        | NotImplementedType
    ):
        return NotImplemented

    def get_status(self, conn_check=True, login=False) -> Status | None:
        """
        tries to fetch provider data, and if successful returns a status string, else None
        if both `conn_check` and `login` are True, also tries to log in automatically
        """
        try:
            self.logger.info(f"Getting status")
            if conn_check:
                if not self._is_connected():
                    self.logger.debug("Skipping, not connected to WiFi")
                    return None
                res = "error"
                try:
                    res = self.attempt_login()
                except:
                    self.logger.exception("Automatic login failed")
                finally:
                    if res == NotImplemented:
                        self.logger.debug("Automatic login not implemented")
                    elif res == "success":
                        self.logger.info("Automatic login successful")
                    elif res == "already_logged_in":
                        self.logger.debug("Already logged in")
                    else:
                        self.logger.warn("Automatic login failed")
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
            self.logger.exception("Unhandled exception while retrieving status")

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
