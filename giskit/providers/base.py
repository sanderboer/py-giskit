"""Base Provider class for data providers.

A Provider represents an organization/service that offers spatial data:
- PDOK (Netherlands)
- OpenStreetMap
- Copernicus (EU)
- USGS (USA)
- etc.

Each provider can support multiple protocols (e.g., PDOK supports OGC Features, WFS, WMTS).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd

from giskit.core.recipe import Dataset, Location
from giskit.protocols.base import Protocol


class Provider(ABC):
    """Abstract base class for all data providers."""

    def __init__(self, name: str, **kwargs: Any):
        """Initialize provider.

        Args:
            name: Provider identifier (e.g., 'pdok', 'osm')
            **kwargs: Provider-specific configuration
        """
        self.name = name
        self.config = kwargs
        self._protocols: dict[str, Protocol] = {}

    @abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """Get provider metadata.

        Returns:
            Dictionary with provider info:
            {
                "name": str,
                "description": str,
                "homepage": str,
                "services": list[str],
                "coverage": str,  # e.g., "Netherlands", "Global"
                "attribution": str
            }
        """
        pass

    @abstractmethod
    async def download_dataset(
        self,
        dataset: Dataset,
        location: Location,
        output_path: Path,
        output_crs: str = "EPSG:4326",
        **kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """Download a dataset for a specific location.

        Args:
            dataset: Dataset specification from recipe
            location: Location specification from recipe
            output_path: Where to save downloaded data
            output_crs: Output coordinate reference system
            **kwargs: Additional download options

        Returns:
            GeoDataFrame with downloaded data

        Raises:
            ValueError: If dataset configuration is invalid
            NotImplementedError: If provider doesn't support this dataset type
        """
        pass

    @abstractmethod
    def get_supported_services(self) -> list[str]:
        """Get list of supported services.

        Returns:
            List of service names (e.g., ['bgt', 'bag', 'bag3d'] for PDOK)
        """
        pass

    @abstractmethod
    def get_supported_protocols(self) -> list[str]:
        """Get list of supported protocols.

        Returns:
            List of protocol names (e.g., ['ogc-features', 'wfs', 'wmts'])
        """
        pass

    def register_protocol(self, name: str, protocol: Protocol) -> None:
        """Register a protocol instance for this provider.

        Args:
            name: Protocol identifier
            protocol: Protocol instance
        """
        self._protocols[name] = protocol

    def get_protocol(self, name: str) -> Optional[Protocol]:
        """Get a registered protocol instance.

        Args:
            name: Protocol identifier

        Returns:
            Protocol instance or None if not registered
        """
        return self._protocols.get(name)

    async def __aenter__(self) -> "Provider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        # Clean up all protocols
        for protocol in self._protocols.values():
            await protocol.__aexit__(exc_type, exc_val, exc_tb)


class ProviderRegistry:
    """Registry for all available providers."""

    def __init__(self) -> None:
        """Initialize empty provider registry."""
        self._providers: dict[str, type[Provider]] = {}

    def register(self, name: str, provider_class: type[Provider]) -> None:
        """Register a provider class.

        Args:
            name: Provider identifier (e.g., 'pdok')
            provider_class: Provider class (not instance)
        """
        self._providers[name] = provider_class

    def get(self, name: str) -> Optional[type[Provider]]:
        """Get a provider class by name.

        Args:
            name: Provider identifier

        Returns:
            Provider class or None if not found
        """
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """Get list of registered provider names.

        Returns:
            List of provider identifiers
        """
        return list(self._providers.keys())

    def create(self, name: str, **kwargs: Any) -> Provider:
        """Create a provider instance.

        Args:
            name: Provider identifier
            **kwargs: Provider-specific configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_class = self.get(name)
        if provider_class is None:
            raise ValueError(
                f"Provider '{name}' not found. Available: {', '.join(self.list_providers())}"
            )
        return provider_class(name=name, **kwargs)


# Global provider registry
_registry = ProviderRegistry()


def register_provider(name: str, provider_class: type[Provider]) -> None:
    """Register a provider in the global registry.

    Args:
        name: Provider identifier
        provider_class: Provider class
    """
    _registry.register(name, provider_class)


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Get a provider instance from the global registry.

    Args:
        name: Provider identifier
        **kwargs: Provider configuration

    Returns:
        Provider instance
    """
    return _registry.create(name, **kwargs)


def list_providers() -> list[str]:
    """List all registered providers.

    Returns:
        List of provider identifiers
    """
    return _registry.list_providers()
