import argparse
import json
import logging
import sys

from .providers import PROVIDERS


parser = argparse.ArgumentParser(
    prog="waybar-trains",
    description="display information from a train's WiFi network on your Waybar",
)

parser.add_argument(
    "--no-conn-check",
    action="store_true",
    help="Do not heuristically check if connected to train network",
)

parser.add_argument(
    "--verbose", "-v", action="store_true", help="Output debug information to stderr"
)

args = parser.parse_args()


logging.basicConfig(
    format="%(asctime)s  [%(levelname)-8s] %(name)-13s - %(message)s",
    stream=sys.stderr,
    level=logging.DEBUG if args.verbose else logging.CRITICAL,
)
logger = logging.getLogger("waybar-trains")


for provider_class in PROVIDERS:
    provider = provider_class(logger)
    status = provider.get_status(conn_check=not args.no_conn_check)
    if status is not None:
        print(
            json.dumps(
                {
                    "text": status.get_text(),
                    # "alt": "$alt",
                    "tooltip": status.get_tooltip(),
                    "class": f"provider-{provider.name}",
                }
            )
        )
        break
