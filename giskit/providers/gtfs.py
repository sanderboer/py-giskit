"""GTFS Provider for public transport data.

Provides access to public transport stops/stations via GTFS feeds.
"""

from pathlib import Path
from typing import Any

import geopandas as gpd

from giskit.core.recipe import Dataset, Location
from giskit.protocols.gtfs import GTFSProtocol
from giskit.providers.base import Provider, register_provider


class GTFSProvider(Provider):
    """Provider for GTFS (General Transit Feed Specification) data.

    Supports downloading public transport stop locations from GTFS feeds.
    Data is cached locally (default: 1 day) to minimize downloads.

    Example:
        >>> provider = GTFSProvider("ndov")
        >>> location = Location(type="bbox", coordinates=[4.8, 52.3, 4.9, 52.4])
        >>> dataset = Dataset(service="haltes", location=location)
        >>> stops = await provider.download_dataset(dataset)
    """

    def __init__(
        self,
        name: str,
        gtfs_url: str | None = None,
        cache_days: int = 1,
        **kwargs: Any,
    ):
        """Initialize GTFS provider.

        Args:
            name: Provider name (e.g., "ndov")
            gtfs_url: URL to GTFS zip file (loaded from config if not provided)
            cache_days: Days to cache GTFS data (default: 1)
            **kwargs: Additional configuration
        """
        super().__init__(name, **kwargs)

        # Load config if gtfs_url not provided
        if gtfs_url is None:
            from giskit.config.discovery import get_provider_config
            import yaml

            provider_meta = get_provider_config(name)
            if provider_meta is None:
                raise ValueError(f"No config found for provider '{name}' and no gtfs_url provided")

            # Load full config file to get gtfs_url
            config_file = provider_meta.get("config_file")
            if not config_file:
                raise ValueError(f"No config_file found for provider '{name}'")

            with open(config_file) as f:
                full_config = yaml.safe_load(f)

            gtfs_url = full_config.get("gtfs_url")
            if not gtfs_url:
                raise ValueError(f"No gtfs_url found in config for provider '{name}'")

            # Get cache_days from config if specified
            cache_days = full_config.get("cache_days", cache_days)

        self.gtfs_url = gtfs_url
        self.cache_days = cache_days

        # Create protocol instance
        self.protocol = GTFSProtocol(
            base_url=gtfs_url,
            cache_days=cache_days,
        )

        # Metadata
        self.metadata = {
            "name": name.upper(),
            "title": f"{name.upper()} - Public Transport Data",
            "description": "Public transport stops and stations from GTFS feed",
            "coverage": "Netherlands",
            "url": gtfs_url,
        }

    async def get_metadata(self) -> dict[str, Any]:
        """Get provider metadata."""
        # Try to enrich with actual capabilities
        try:
            caps = await self.protocol.get_capabilities()
            return {
                **self.metadata,
                "stop_count": caps.get("stop_count", 0),
                "bbox": caps.get("bbox"),
            }
        except Exception:
            return self.metadata

    def get_supported_services(self) -> list[str]:
        """Get list of supported services.

        Returns:
            List with single service: ["haltes"]
        """
        return ["haltes"]

    def get_service_info(self, service_id: str) -> dict[str, Any]:
        """Get service metadata.

        Args:
            service_id: Service identifier (must be "haltes")

        Returns:
            Service metadata
        """
        if service_id != "haltes":
            raise ValueError(f"Unknown service: {service_id}. Only 'haltes' is supported.")

        return {
            "id": "haltes",
            "name": "haltes",
            "title": "OV Haltes (Public Transport Stops)",
            "description": (
                "Public transport stops and stations including bus, tram, metro, "
                "train, and ferry. Updated daily from GTFS feed."
            ),
            "protocol": "gtfs",
            "category": "infrastructure",
            "keywords": ["ov", "openbaar vervoer", "haltes", "stations", "gtfs"],
            "url": self.gtfs_url,
            "format": "geojson",
        }

    async def download_dataset(
        self,
        dataset: Dataset,
        location: Location,
        output_path: Path,
        output_crs: str = "EPSG:28992",
        **kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """Download public transport stops.

        Args:
            dataset: Dataset specification
            location: Location specification
            output_path: Output path (not used for GTFS, data returned in memory)
            output_crs: Target CRS (default: EPSG:28992 / RD)
            **kwargs: Additional parameters

        Returns:
            GeoDataFrame with stops in specified CRS
        """
        from giskit.core.spatial import buffer_point_to_bbox, transform_bbox

        # Convert location to bbox
        if location.type == "bbox":
            bbox_rd = tuple(location.value)
        elif location.type == "point":
            # Get radius from location or kwargs
            radius = location.radius or kwargs.get("radius", 1000)
            lon, lat = location.value[:2]
            bbox_rd = buffer_point_to_bbox(lon, lat, radius, crs="EPSG:28992")
        else:
            raise ValueError(f"Unsupported location type: {location.type}")

        # Transform bbox from RD to WGS84 for GTFS query
        bbox_wgs84 = transform_bbox(bbox_rd, from_crs="EPSG:28992", to_crs="EPSG:4326")

        # Download stops
        gdf = await self.protocol.get_features(
            bbox=bbox_wgs84,
            crs=output_crs,  # Request output in target CRS
        )

        return gdf

    def get_supported_protocols(self) -> list[str]:
        """Get list of supported protocols.

        Returns:
            List with single protocol: ["gtfs"]
        """
        return ["gtfs"]

    def list_categories(self) -> list[str]:
        """Get list of all service categories.

        Returns:
            List with single category: ["infrastructure"]
        """
        return ["infrastructure"]

    def get_services_by_category(self, category: str) -> list[str]:
        """Get services in a specific category.

        Args:
            category: Category name

        Returns:
            List of service IDs if category matches, empty list otherwise
        """
        if category == "infrastructure":
            return ["haltes"]
        return []


# Register provider
register_provider("ndov", GTFSProvider)


__all__ = ["GTFSProvider"]
