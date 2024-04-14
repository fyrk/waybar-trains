from .base import BaseProvider
from .iceportal import IceportalProvider
from .odeg import ODEGProvider

PROVIDERS: list[type[BaseProvider]] = [
    IceportalProvider,
    ODEGProvider,
]
