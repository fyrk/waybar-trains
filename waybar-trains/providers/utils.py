import logging
import socket
from datetime import datetime, timedelta
from functools import lru_cache

from pyroute2.iwutil import IW
from pyroute2.netlink import nl80211

from .types import Stop

_logger = logging.getLogger("waybar-trains")


@lru_cache
def _get_connected_ssids() -> set[str]:
    # copied from https://github.com/e1mo/waybar-iceportal/blob/13b297c2cc0b4b56d4caccd626a16b455d8d49e5/waybar-iceportal#L48
    ssids = set()
    with IW() as iw:
        interfaces = [v[0] for v in iw.get_interfaces_dict().values()]
        for ifindex in interfaces:
            bss: nl80211.nl80211cmd | None = iw.get_associated_bss(ifindex)
            if bss is None:
                continue
            attr_bss: nl80211.nl80211cmd.bss | None = bss.get_attr("NL80211_ATTR_BSS")
            if attr_bss is None:
                continue
            info: list[dict] = attr_bss.get_attrs("NL80211_BSS_INFORMATION_ELEMENTS")
            ssids |= set([d["SSID"].decode("utf-8") for d in info])
    _logger.debug(f"Found WiFi networks {ssids}")
    return ssids


def is_connected_to_ssid(ssids: set[str]):
    # check if connected to train network
    return not ssids.isdisjoint(_get_connected_ssids())


def resolve_hostname(host: str) -> str:
    return socket.getaddrinfo(
        host=host,
        port=443,
        family=socket.AF_INET,
        proto=socket.IPPROTO_TCP,
    )[0][4][0]


def estimate_next_stop(stops: list[Stop], now: datetime | None = None):
    if now is None:
        now = datetime.now().astimezone()
    for stop in stops:
        time = stop.estimated_departure()
        if time and time.real > now:
            return stop

    # show last stop for up to 30 minutes after stop's time
    if stops:
        time = stops[-1].estimated_departure()
        if time and time.real + timedelta(minutes=30) > now:
            return stops[-1]
