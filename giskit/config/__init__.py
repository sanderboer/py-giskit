"""GISKit configuration package.

Configuration loaders for services and quirks.
"""

from giskit.config.discovery import (
    discover_providers,
    get_provider_config,
    list_providers,
)
from giskit.config.loader import (
    QuirkDefinition,
    QuirksConfig,
    ServiceDefinition,
    ServicesConfig,
    load_quirks,
    load_services,
    save_quirks,
    save_services,
)

__all__ = [
    "load_services",
    "load_quirks",
    "save_services",
    "save_quirks",
    "ServiceDefinition",
    "ServicesConfig",
    "QuirkDefinition",
    "QuirksConfig",
    "discover_providers",
    "get_provider_config",
    "list_providers",
]
