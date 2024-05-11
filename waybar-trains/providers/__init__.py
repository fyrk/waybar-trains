from .base import BaseProvider
from .iceportal import IceportalProvider
from .odeg import ODEGProvider
from .zugportal import ZugportalProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    provider.NAME: provider
    for provider in [
        IceportalProvider,
        ZugportalProvider,
        ODEGProvider,
    ]
}
