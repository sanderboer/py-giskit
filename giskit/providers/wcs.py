"""WCS Provider - Config-driven provider for coverage/elevation data.

This provider supports WCS (Web Coverage Service) for downloading
raster coverage data like:
- Elevation models (DTM, DSM)
- AHN (Actueel Hoogtebestand Nederland)
- Temperature/climate data
- Other gridded/raster coverage data

For other protocols, use:
- OGCFeaturesProvider for vector data (OGC API Features)
- WMTSProvider for pre-rendered tile imagery
- WMSProvider for dynamic map rendering (not yet implemented)

Examples:
    >>> # Use with PDOK AHN elevation data
    >>> provider = WCSProvider("pdok-wcs")
    >>> services = provider.get_supported_services()
    >>>
    >>> # Use with custom WCS service
    >>> # Just create config/services/my-wcs.yml
    >>> provider = WCSProvider("my-wcs")
    >>> services = provider.get_supported_services()
"""

from pathlib import Path
from typing import Any

import geopandas as gpd

from giskit.config import load_services
from giskit.core.recipe import Dataset, Location
from giskit.protocols.wcs import WCSProtocol
from giskit.providers.base import Provider, register_provider


class WCSProvider(Provider):
    """WCS provider for coverage/elevation data.

    Loads services from YAML config files, making it work with any provider
    that offers WCS endpoints (raster coverage data).

    Supports:
    - WCS (Web Coverage Service)
    - Elevation data (DTM, DSM)
    - AHN lidar data
    - Climate/weather grids
    - Other gridded raster data

    Does NOT support:
    - Vector data (use OGCFeaturesProvider instead)
    - Pre-rendered tiles (use WMTSProvider instead)
    """

    def __init__(self, name: str, **kwargs: Any):
        """Initialize WCS provider.

        Args:
            name: Provider identifier (e.g., "pdok-wcs", "my-wcs")
                  Must have corresponding config/services/{name}.yml
            **kwargs: Additional configuration

        Raises:
            FileNotFoundError: If config file not found and no fallback provided
            ValueError: If config is invalid
        """
        super().__init__(name, **kwargs)

        # Load services from config
        fallback = kwargs.get("fallback_services", None)
        self.services = load_services(name, fallback=fallback)

        if not self.services:
            raise ValueError(
                f"No services found for provider '{name}'. "
                f"Check config/services/{name}.yml exists and is valid."
            )

        # Register WCS protocols for each service/coverage
        self.protocols: dict[str, WCSProtocol] = {}

        for service_name, service_config in self.services.items():
            if isinstance(service_config, dict):
                url = service_config.get("url", "")
                coverages = service_config.get("coverages", {})
                native_crs = service_config.get("native_crs", "EPSG:28992")
                native_resolution = service_config.get("native_resolution")

                # Register protocol for each coverage
                for coverage_key, coverage_id in coverages.items():
                    # Create protocol key: service.coverage (e.g., "ahn.dsm", "ahn.dtm")
                    protocol_key = f"{service_name}.{coverage_key}"

                    self.protocols[protocol_key] = WCSProtocol(
                        base_url=url,
                        coverage_id=coverage_id,
                        native_crs=native_crs,
                        native_resolution=native_resolution,
                    )

        print("✅ WCSProvider initialized")
        print(f"   Loaded {len(self.services)} services from config")
        print(f"   Registered {len(self.protocols)} coverage protocols")
        print(f"   Available coverages: {list(self.protocols.keys())}")

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
            "description": f"WCS provider: {self.name}",
            "protocol": "wcs",
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
            **kwargs: Additional download options (e.g., resolution, format)

        Returns:
            GeoDataFrame with downloaded coverage data metadata

        Raises:
            ValueError: If service not found
            NotImplementedError: Protocol not yet implemented
        """
        # Parse dataset name: "service.coverage" (e.g., "ahn.dtm", "ahn.dsm")
        service_name = dataset.service or ""
        if "." not in service_name:
            raise ValueError(
                f"WCS dataset must be in format 'service.coverage' (e.g., 'ahn.dtm'). "
                f"Got: '{service_name}'"
            )

        protocol_key = service_name

        if protocol_key not in self.protocols:
            raise ValueError(
                f"Coverage '{protocol_key}' not found. "
                f"Available coverages: {', '.join(self.protocols.keys())}"
            )

        # Get protocol
        protocol = self.protocols[protocol_key]

        # For now, assume location is already a bbox in EPSG:28992
        # TODO: Add proper location conversion for other types
        if location.type.value != "bbox":
            raise NotImplementedError(
                f"Location type '{location.type.value}' not yet supported for WCS. "
                "Use bbox for now."
            )

        if not isinstance(location.value, list) or len(location.value) != 4:
            raise ValueError("Location value must be [minx, miny, maxx, maxy] for bbox")

        # Extract bbox values (location.value is Union[str, list[float], list[list[float]]])
        bbox_values = location.value
        if not all(isinstance(v, (int, float)) for v in bbox_values):
            raise ValueError("All bbox values must be numbers")

        bbox: tuple[float, float, float, float] = (
            bbox_values[0],  # type: ignore
            bbox_values[1],  # type: ignore
            bbox_values[2],  # type: ignore
            bbox_values[3],  # type: ignore
        )

        # Get resolution from dataset or use default
        resolution = dataset.resolution or protocol.native_resolution or 0.5

        # Create output filename
        coverage_name = protocol_key.replace(".", "_")
        output_file = output_path / f"{coverage_name}.tif"

        # Download coverage as GeoTIFF
        print(f"📥 Downloading {protocol_key}...")
        print(f"   Resolution: {resolution}m")
        print(f"   Bbox: {bbox}")

        def progress(msg: str, pct: float):
            """Simple progress callback."""
            print(f"   [{pct*100:.0f}%] {msg}")

        saved_path = await protocol.save_coverage_as_geotiff(
            bbox=bbox,
            output_path=output_file,
            resolution=resolution,
            crs="EPSG:28992",
            progress_callback=progress,
        )

        print(f"✅ Saved to: {saved_path}")

        # Return GeoDataFrame with metadata
        # (WCS returns raster data, but we return metadata as GeoDataFrame for consistency)
        from shapely.geometry import box

        gdf = gpd.GeoDataFrame(
            {
                "coverage": [protocol_key],
                "file": [str(saved_path)],
                "resolution": [resolution],
            },
            geometry=[box(*bbox)],
            crs="EPSG:28992",
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
        return ["wcs"]

    def get_services_by_category(self, category: str) -> list[str]:
        """Get list of services in a specific category.

        Args:
            category: Category name (e.g., 'elevation', 'climate')

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


# Register WCS provider globally
register_provider("wcs", WCSProvider)
