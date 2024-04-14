import json
from datetime import datetime, timedelta
from typing import Any

from .base import BaseProvider
from .types import DelayedTime, Status, Stop


class ODEGProvider(BaseProvider):
    @property
    def name(self):
        return "odeg"

    def _fetch_data(self) -> Any:
        with open("_data/2024-04-13-20-20-00-odeg-re1/graphql.json") as f:
            data = json.load(f)
        widget = json.loads(data["data"]["feed_widget"]["widget"]["json"])
        return widget

    def _get_status_from_data(self, data: Any) -> Status | None:
        def json_to_stop(stop: dict):
            # TODO: is stop["track"] always empty or does it sometimes contain the track?
            return Stop(
                name=stop["name"],
                arrival=DelayedTime.from_iso(
                    stop.get("arrivalPlanned"),
                    stop.get("arrivalDelay"),
                ),
                departure=DelayedTime.from_iso(
                    stop.get("arrivalPlanned"),
                    stop.get("arrivalDelay"),
                ),
            )

        def estimate_next_stop(stops: list[Stop]):
            # now = datetime.now().astimezone()
            now = datetime(2024, 4, 13, 20, 20, 0).astimezone()
            next_stop = None
            for next_stop in stops:
                if next_stop.departure:
                    stop_time = next_stop.departure
                elif next_stop.arrival:
                    stop_time = next_stop.arrival
                else:
                    continue
                if stop_time.real > now:
                    break
            return next_stop

        data = data["course"]

        stops = [json_to_stop(stop) for stop in data["stops"]]
        next_stop = estimate_next_stop(stops)
        return Status(
            line=data["line"],
            line_id=data["id"],
            origin=data["origin"],
            destination=data["destination"],
            next_stop=next_stop,
            stops=stops,
        )
