import json
from datetime import datetime
from typing import Any

import requests

from .base import BaseProvider
from .types import DelayedTime, Status, Stop
from .utils import is_connected_to_ssid


class ODEGProvider(BaseProvider):
    @property
    def name(self):
        return "odeg"

    def _is_connected(self) -> bool:
        return is_connected_to_ssid({"ODEG Free WiFi"})

    def _fetch_data(self) -> Any:
        response = requests.post(
            "https://wasabi.hotspot-local.unwired.at/api/graphql",
            json={
                "operationName": "feed_widget",
                "variables": {
                    "widget_id": "cc0504a8-8c1d-4898-b7e1-8eb1ca72f3be",
                    "language": "en",
                    "user_session_id": "e9fba063-7f3b-4131-adfc-6ce562855be1",
                },
                "query": "query feed_widget($user_session_id: ID, $ap_mac: String, $widget_id: ID!, $language: String) {\n  feed_widget(\n    user_session_id: $user_session_id\n    ap_mac: $ap_mac\n    widget_id: $widget_id\n    language: $language\n  ) {\n    user_session_id\n    error {\n      ...Error\n      __typename\n    }\n    widget {\n      ...Widget\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment Error on Error {\n  error_code\n  error_message\n  __typename\n}\n\nfragment Widget on Widget {\n  widget_id\n  page_id\n  position\n  date_updated\n  ... on SimpleTextWidget {\n    is_ready\n    ...SimpleTextWidget\n    __typename\n  }\n  ... on ConnectWidget {\n    button_text\n    connected_text\n    variant\n    confirmation\n    delay\n    require_sms_auth\n    email_mandatory\n    terms_of_service\n    store_terms\n    enable_anchor\n    anchor {\n      ...Anchor\n      __typename\n    }\n    __typename\n  }\n  ... on JourneyInfoWidget {\n    json\n    enable_anchor\n    anchor {\n      ...Anchor\n      __typename\n    }\n    variant\n    is_ready\n    hold_text\n    __typename\n  }\n  ... on StructuredTextWidget {\n    is_ready\n    categories {\n      ...StructuredTextCategory\n      __typename\n    }\n    __typename\n  }\n  ... on SupportFormWidget {\n    custom_options {\n      option_key\n      text\n      email\n      __typename\n    }\n    __typename\n  }\n  ... on Wifi4EUWidget {\n    self_test\n    network_identifier\n    __typename\n  }\n  ... on EmergencyRequestWidget {\n    reasons {\n      reason\n      __typename\n    }\n    disclaimer\n    status\n    __typename\n  }\n  ... on MovingMapWidget {\n    is_ready\n    icon\n    geo_points {\n      icon_width\n      icon_url\n      lat\n      long\n      text\n      __typename\n    }\n    json\n    __typename\n  }\n  __typename\n}\n\nfragment Anchor on Anchor {\n  slug\n  label\n  __typename\n}\n\nfragment SimpleTextWidget on SimpleTextWidget {\n  content\n  enable_anchor\n  anchor {\n    ...Anchor\n    __typename\n  }\n  __typename\n}\n\nfragment StructuredTextCategory on StructuredTextCategory {\n  label\n  entries {\n    ...StructuredTextEntry\n    __typename\n  }\n  enable_anchor\n  anchor {\n    ...Anchor\n    __typename\n  }\n  __typename\n}\n\nfragment StructuredTextEntry on StructuredTextEntry {\n  title\n  content\n  POI_match {\n    ...PoiMatch\n    __typename\n  }\n  __typename\n}\n\nfragment PoiMatch on PoiMatch {\n  stop {\n    name\n    id\n    ds100\n    ibnr\n    __typename\n  }\n  __typename\n}",
            },
        )
        widget = json.loads(response.json()["data"]["feed_widget"]["widget"]["json"])
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
            now = datetime.now().astimezone()
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
