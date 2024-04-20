from functools import lru_cache
from pyroute2.netlink import nl80211
from pyroute2.iwutil import IW


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
    return ssids


def is_connected_to_ssid(ssids: set[str]):
    # check if connected to train network
    return not ssids.isdisjoint(_get_connected_ssids())
