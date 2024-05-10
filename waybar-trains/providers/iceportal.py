import socket
from typing import NamedTuple

import requests

from .base import BaseProvider
from .types import DelayedTime, Status, Stop
from .utils import is_connected_to_ssid


class IceportalData(NamedTuple):
    trip: dict
    status: dict


class IceportalProvider(BaseProvider):
    @property
    def name(self):
        return "iceportal"

    def _is_connected(self) -> bool:
        if not is_connected_to_ssid({"WIFI@DB", "WIFIonICE"}):
            return False

        # check if iceportal.de with local ip address is really available
        # idea from https://github.com/liclac/ambient/blob/75e1d3aee4c1c5ba55d95cf9e14e39afb24879b1/functions.d/ambient_resolve4.fish
        ip = socket.getaddrinfo(
            host="iceportal.de",
            port=443,
            family=socket.AF_INET,
            proto=socket.IPPROTO_TCP,
        )[0][4][0]
        return ip.startswith("172.")

    def _fetch_data(self) -> IceportalData:
        return IceportalData(
            trip=requests.get("https://iceportal.de/api1/rs/tripInfo/trip").json(),
            status=requests.get("https://iceportal.de/api1/rs/status").json(),
        )

    def _get_status_from_data(self, data: IceportalData) -> Status | None:
        def json_to_stop(stop: dict):
            station = stop["station"]
            timetable = stop["timetable"]
            return Stop(
                name=station["name"],
                arrival=DelayedTime.from_timestamps_ns(
                    timetable["scheduledArrivalTime"],
                    timetable["actualArrivalTime"],
                ),
                departure=DelayedTime.from_timestamps_ns(
                    timetable["scheduledDepartureTime"],
                    timetable["actualDepartureTime"],
                ),
                id=station["evaNr"],
            )

        trip = data.trip["trip"]
        status = data.status

        stops = [json_to_stop(stop) for stop in trip["stops"]]
        next_stop_id = trip["stopInfo"]["actualNext"]
        next_stop = next(stop for stop in stops if stop.id == next_stop_id)
        return Status(
            line_id=trip["vzn"],
            vehicle=trip["trainType"],
            destination=trip["stopInfo"]["finalStationName"],
            wagon_class=status["wagonClass"].lower(),
            speed=status["speed"],
            stops=stops,
            next_stop=next_stop,
        )
