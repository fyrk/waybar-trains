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
                "query": _ODEG_QUERY,
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
                    stop.get("departurePlanned"),
                    stop.get("departureDelay"),
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


_ODEG_QUERY = """
query feed_widget($user_session_id: ID, $ap_mac: String, $widget_id: ID!, $language: String) {
  feed_widget(
    user_session_id: $user_session_id
    ap_mac: $ap_mac
    widget_id: $widget_id
    language: $language
  ) {
    user_session_id
    error {
      ...Error
      __typename
    }
    widget {
      ...Widget
      __typename
    }
    __typename
  }
}

fragment Error on Error {
  error_code
  error_message
  __typename
}

fragment Widget on Widget {
  widget_id
  page_id
  position
  date_updated
  ... on SimpleTextWidget {
    is_ready
    ...SimpleTextWidget
    __typename
  }
  ... on ConnectWidget {
    button_text
    connected_text
    variant
    confirmation
    delay
    require_sms_auth
    email_mandatory
    terms_of_service
    store_terms
    enable_anchor
    anchor {
      ...Anchor
      __typename
    }
    __typename
  }
  ... on JourneyInfoWidget {
    json
    enable_anchor
    anchor {
      ...Anchor
      __typename
    }
    variant
    is_ready
    hold_text
    __typename
  }
  ... on StructuredTextWidget {
    is_ready
    categories {
      ...StructuredTextCategory
      __typename
    }
    __typename
  }
  ... on SupportFormWidget {
    custom_options {
      option_key
      text
      email
      __typename
    }
    __typename
  }
  ... on Wifi4EUWidget {
    self_test
    network_identifier
    __typename
  }
  ... on EmergencyRequestWidget {
    reasons {
      reason
      __typename
    }
    disclaimer
    status
    __typename
  }
  ... on MovingMapWidget {
    is_ready
    icon
    geo_points {
      icon_width
      icon_url
      lat
      long
      text
      __typename
    }
    json
    __typename
  }
  __typename
}

fragment Anchor on Anchor {
  slug
  label
  __typename
}

fragment SimpleTextWidget on SimpleTextWidget {
  content
  enable_anchor
  anchor {
    ...Anchor
    __typename
  }
  __typename
}

fragment StructuredTextCategory on StructuredTextCategory {
  label
  entries {
    ...StructuredTextEntry
    __typename
  }
  enable_anchor
  anchor {
    ...Anchor
    __typename
  }
  __typename
}

fragment StructuredTextEntry on StructuredTextEntry {
  title
  content
  POI_match {
    ...PoiMatch
    __typename
  }
  __typename
}

fragment PoiMatch on PoiMatch {
  stop {
    name
    id
    ds100
    ibnr
    __typename
  }
  __typename
}"""
