"""OGC API Features Provider - Config-driven provider for OGC API Features.

This is a generic provider that loads services and quirks from YAML config files.
It supports OGC API Features (vector data) endpoints only.

For other protocols, use:
- WMSProvider for raster tiles (WMS/WMTS)
- WFSProvider for legacy Web Feature Service
- WCSProvider for coverage/raster data

Examples:
    >>> # Use with PDOK
    >>> provider = OGCFeaturesProvider("pdok")
    >>> services = provider.get_supported_services()
    >>>
    >>> # Use with custom provider
    >>> # Just create config/services/myapi.yml
    >>> provider = OGCFeaturesProvider("myapi")
    >>> services = provider.get_supported_services()

This replaces hardcoded provider classes like PDOKProvider.
"""

from pathlib import Path
from typing import Any

import geopandas as gpd

from giskit.config import load_services
from giskit.core.recipe import Dataset, Location
from giskit.protocols.ogc_features import OGCFeaturesProtocol
from giskit.protocols.quirks import get_format_quirks, get_quirks
from giskit.providers.base import Provider, register_provider


class OGCFeaturesProvider(Provider):
    """OGC API Features provider.

    Loads services from YAML config files, making it work with any provider
    that offers OGC API Features endpoints (vector data).

    Supports:
    - GeoJSON format
    - CityJSON format (3D buildings)
    - Feature collections with attributes

    Does NOT support:
    - Raster data (use WMSProvider instead)
    - Legacy WFS (use WFSProvider instead)
    - Coverage data (use WCSProvider instead)
    """

    def __init__(self, name: str, **kwargs: Any):
        """Initialize OGC API Features provider.

        Args:
            name: Provider identifier (e.g., "pdok", "myapi")
                  Must have corresponding config/services/{name}.yml
            **kwargs: Additional configuration

        Raises:
            FileNotFoundError: If config file not found and no fallback provided
            ValueError: If config is invalid
        """
        super().__init__(name, **kwargs)

        # Load services from config
        # If config file doesn't exist, this will raise FileNotFoundError
        # (unless user provides fallback in kwargs)
        fallback = kwargs.get("fallback_services", None)
        self.services = load_services(name, fallback=fallback)

        if not self.services:
            raise ValueError(
                f"No services found for provider '{name}'. "
                f"Check config/services/{name}.yml exists and is valid."
            )

        # Get provider-level quirks
        provider_quirks = get_quirks(name, "ogc-features")

        # Register OGC Features protocols for each service
        for service_name, service_config in self.services.items():
            # Handle both old string format and new dict format
            if isinstance(service_config, str):
                service_url = service_config
                service_format = None
            else:
                service_url = service_config["url"]
                service_format = service_config.get("format", None)

            # Apply format-specific quirks if specified
            if service_format:
                # Merge provider quirks with format quirks
                format_quirks = get_format_quirks(service_format)
                # For now, just use format quirks (TODO: merge logic)
                quirks = format_quirks
            else:
                quirks = provider_quirks

            # Create and register protocol for this service
            protocol = OGCFeaturesProtocol(base_url=service_url, quirks=quirks)
            self.register_protocol(f"ogc-features-{service_name}", protocol)

    async def get_metadata(self) -> dict[str, Any]:
        """Get provider metadata.

        Returns:
            Dictionary with provider information
        """
        # Count services by category
        categories: dict[str, int] = {}
        for service_config in self.services.values():
            if isinstance(service_config, dict):
                category = service_config.get("category", "other")
                categories[category] = categories.get(category, 0) + 1

        return {
            "name": self.name,
            "description": f"OGC API Features provider: {self.name}",
            "total_services": len(self.services),
            "categories": categories,
            "services": list(self.services.keys()),
        }

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
            ValueError: If service not found
        """
        # Get service from dataset
        service = dataset.service
        if service not in self.services:
            raise ValueError(
                f"Service '{service}' not found for provider '{self.name}'. "
                f"Available: {', '.join(self.services.keys())}"
            )

        # Get protocol for this service
        protocol_name = f"ogc-features-{service}"
        protocol = self.get_protocol(protocol_name)

        if protocol is None:
            raise ValueError(f"Protocol not registered: {protocol_name}")

        # Convert location to bbox
        bbox = location.to_bbox()

        # Get temporal filter from dataset (default to 'latest')
        temporal = dataset.temporal if hasattr(dataset, "temporal") and dataset.temporal else "latest"

        # Download features using OGC API
        async with protocol:
            gdf = await protocol.get_features(
                bbox=bbox,  # type: ignore
                layers=dataset.layers,
                crs=output_crs,
                temporal=temporal,
                **kwargs,
            )

        return gdf

    def get_supported_services(self) -> list[str]:
        """Get list of supported services.

        Returns:
            List of service names
        """
        return list(self.services.keys())

    def get_supported_protocols(self) -> list[str]:
        """Get list of supported protocols.

        Returns:
            List of protocol names
        """
        return ["ogc-features"]

    def get_services_by_category(self, category: str) -> list[str]:
        """Get list of services in a specific category.

        Args:
            category: Category name (e.g., 'base_registers', 'topography', 'statistics')

        Returns:
            List of service names in this category
        """
        services = []
        for service_name, service_config in self.services.items():
            if isinstance(service_config, dict):
                if service_config.get("category") == category:
                    services.append(service_name)
        return services

    def get_service_info(self, service: str) -> dict[str, Any]:
        """Get detailed information about a specific service.

        Args:
            service: Service name

        Returns:
            Dictionary with service metadata

        Raises:
            ValueError: If service not found
        """
        if service not in self.services:
            raise ValueError(
                f"Service '{service}' not found. " f"Available: {', '.join(self.services.keys())}"
            )

        service_config = self.services[service]
        if isinstance(service_config, str):
            # Old format - just URL
            return {
                "name": service,
                "url": service_config,
                "title": service.upper(),
                "category": "unknown",
                "description": "",
                "keywords": [],
            }
        else:
            # New format - full metadata
            return {"name": service, **service_config}

    def list_categories(self) -> list[str]:
        """Get list of all service categories.

        Returns:
            List of category names
        """
        categories = set()
        for service_config in self.services.values():
            if isinstance(service_config, dict):
                category = service_config.get("category", "other")
                categories.add(category)
        return sorted(categories)


# Register OGC API Features provider globally
register_provider("ogc-features", OGCFeaturesProvider)
