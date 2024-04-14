import json

from .providers import PROVIDERS


for provider_class in PROVIDERS:
    provider = provider_class()
    status = provider.get_status()
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
