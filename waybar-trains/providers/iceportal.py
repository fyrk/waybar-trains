from datetime import datetime
from typing import Literal, NamedTuple
from zoneinfo import ZoneInfo

from .base import BaseProvider, DummyProviderData
from .types import DelayedTime, Status, Stop
from .utils import is_connected_to_ssid, resolve_hostname


class IceportalData(NamedTuple):
    trip: dict
    status: dict


class IceportalProvider(BaseProvider):
    NAME = "iceportal"

    def _is_connected(self) -> bool:
        return (
            is_connected_to_ssid({"WIFIonICE"})
            and
            # check if iceportal.de with local ip address is really available
            # idea from https://github.com/liclac/ambient/blob/75e1d3aee4c1c5ba55d95cf9e14e39afb24879b1/functions.d/ambient_resolve4.fish
            resolve_hostname("iceportal.de").startswith("172.")
        )

    def _fetch_data(self) -> IceportalData:
        return IceportalData(
            trip=self._session.get("https://iceportal.de/api1/rs/tripInfo/trip").json(),
            status=self._session.get("https://iceportal.de/api1/rs/status").json(),
        )

    def _get_dummy_data(self) -> DummyProviderData[IceportalData]:
        return DummyProviderData(
            IceportalData(
                self._read_dummy_data("2021-08-31T12-02-55-ice1601/trip.json"),
                self._read_dummy_data("2021-08-31T12-02-55-ice1601/status.json"),
            ),
            datetime(2021, 8, 31, 12, 2, 55, tzinfo=ZoneInfo("Europe/Berlin")),
        )

    def _get_status_from_data(self, data: IceportalData) -> Status | None:
        def json_to_stop(stop: dict):
            station = stop["station"]
            timetable = stop["timetable"]
            return Stop(
                name=station["name"],
                id=station["evaNr"],
                arrival=DelayedTime.from_timestamps_ms(
                    timetable["scheduledArrivalTime"],
                    timetable["actualArrivalTime"],
                ),
                departure=DelayedTime.from_timestamps_ms(
                    timetable["scheduledDepartureTime"],
                    timetable["actualDepartureTime"],
                ),
                track=stop.get("track", {}).get("actual"),
            )

        trip = data.trip["trip"]
        status = data.status

        stops = [json_to_stop(stop) for stop in trip["stops"]]
        next_stop_id = trip["stopInfo"]["actualNext"]
        next_stop = next(stop for stop in stops if stop.id == next_stop_id)
        return Status(
            self.NAME,
            line_id=trip["vzn"],
            vehicle=trip["trainType"],
            destination=trip["stopInfo"]["finalStationName"],
            wagon_class=status["wagonClass"].lower(),
            speed=status["speed"],
            stops=stops,
            next_stop=next_stop,
        )

    def attempt_login(
        self,
    ) -> Literal["success"] | Literal["already_logged_in"] | Literal["error"]:
        self.logger.debug("cheching if logged in")
        r = self._session.get("https://login.wifionice.de/en/")
        r.raise_for_status()
        if "Free online access" not in r.text:
            return "already_logged_in"

        csrf = self._session.cookies.get("csrf", domain=".login.wifionice.de", path="/")
        if csrf is None:
            raise ValueError("csrf cookie not found")
        self.logger.debug("logging in")
        r = self._session.post(
            "https://login.wifionice.de/en/",
            {"login": "true", "CSRFToken": csrf},
        )
        r.raise_for_status()

        return "success" if "Free online access" not in r.text else "error"
