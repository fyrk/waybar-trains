import argparse
import json
import logging
import sys

import requests

from .providers import PROVIDERS

parser = argparse.ArgumentParser(
    prog="waybar-trains",
    description="display information from a train's WiFi network on your Waybar",
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    "--no-conn-check",
    action="store_true",
    help="Do not heuristically check if connected to train network",
)

group.add_argument(
    "--login",
    action="store_true",
    help="Try to automatically log in to WiFi networks if connected",
)

parser.add_argument(
    "--dummy",
    choices=PROVIDERS.keys(),
    help="Use dummy data of the given provider",
)

parser.add_argument(
    "--verbose", "-v", action="store_true", help="Output debug information to stderr"
)

parser.add_argument(
    "--human",
    "-H",
    action="store_true",
    help="Output human-readable JSON (incompatible with Waybar)",
)

args = parser.parse_args()


logging.basicConfig(
    format="%(asctime)s  [%(levelname)-8s] %(name)-13s - %(message)s",
    stream=sys.stderr,
    level=logging.DEBUG if args.verbose else logging.CRITICAL,
)
logger = logging.getLogger("waybar-trains")


if args.dummy:
    provider_name = args.dummy
    provider = PROVIDERS[provider_name]()
    status = provider.get_dummy_status()
else:
    session = requests.Session()
    status = None
    provider_name = None
    for provider_class in PROVIDERS.values():
        provider_name = provider_class.NAME
        provider = provider_class(session)
        status = provider.get_status(
            conn_check=not args.no_conn_check, login=args.login
        )
        if status is not None:
            break

if status is not None:
    output = {
        "text": status.get_text(),
        # "alt": "$alt",
        "tooltip": status.get_tooltip(),
        "class": f"provider-{provider_name}",
    }
    print(
        json.dumps(output)
        if not args.human
        else json.dumps(output, indent=2, ensure_ascii=False)
    )
