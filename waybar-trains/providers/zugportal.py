from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from .base import BaseProvider, DummyProviderData
from .types import DelayedTime, Status, Stop
from .utils import is_connected_to_ssid, resolve_hostname


class ZugportalProvider(BaseProvider):
    NAME = "zugportal"

    def _is_connected(self) -> bool:
        return (
            is_connected_to_ssid({"WIFI@DB"})
            and
            # check if zugportal.de with local ip address is really available
            # idea from https://github.com/liclac/ambient/blob/75e1d3aee4c1c5ba55d95cf9e14e39afb24879b1/functions.d/ambient_resolve4.fish
            resolve_hostname("zugportal.de").startswith("192.168.")
        )

    def _fetch_data(self) -> dict:
        return requests.get(
            "https://zugportal.de/@prd/zupo-travel-information/api/public/ri/journey"
        ).json()

    def _get_dummy_data(self) -> DummyProviderData[dict]:
        return DummyProviderData(
            self._read_dummy_data("2024-05-10T19-40-10-db-re4430/journey.json"),
            datetime(2024, 5, 10, 19, 40, 10, tzinfo=ZoneInfo("Europe/Berlin")),
        )

    def _get_status_from_data(self, data: dict) -> Status | None:
        def parse_time(time: dict | None):
            if time is None:
                return None
            return DelayedTime.from_timestamps_ms(
                time["targetTimeInMs"],
                time["predictedTimeInMs"],
            )

        def parse_stop(stop: dict):
            station = stop["station"]
            return Stop(
                name=station["name"],
                id=station["evaNo"],
                arrival=parse_time(stop.get("arrivalTime")),
                departure=parse_time(stop.get("departureTime")),
                track=stop["track"]["prediction"],
            )

        stops = [parse_stop(stop) for stop in data["stops"]]
        return Status(
            self.NAME,
            line=data["name"],
            line_id=data["no"],
            vehicle=data["category"],
            stops=stops,
        )
