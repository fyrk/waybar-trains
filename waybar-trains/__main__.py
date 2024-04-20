import argparse
import json
import traceback

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

args = parser.parse_args()

for provider_class in PROVIDERS:
    provider = provider_class()
    try:
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
    except:
        traceback.print_exc()
