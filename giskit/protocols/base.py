"""Base Protocol class for data download protocols.

A Protocol represents a specific data transfer/query protocol:
- OGC API Features
- WFS (Web Feature Service)
- WMTS (Web Map Tile Service)
- WMS (Web Map Service)
- Overpass API (OpenStreetMap)
- Custom REST APIs
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import geopandas as gpd
import httpx
from shapely.geometry import box


class Protocol(ABC):
    """Abstract base class for all data protocols.

    Provides common HTTP client management for all protocol implementations.
    """

    def __init__(self, base_url: str, timeout: float = 30.0, **kwargs: Any):
        """Initialize protocol.

        Args:
            base_url: Base URL for the service endpoint
            timeout: Request timeout in seconds (default: 30.0)
            **kwargs: Protocol-specific configuration
        """
        self.base_url = base_url
        self.timeout = timeout
        self.config = kwargs
        self._client: Optional[httpx.AsyncClient] = None

    @abstractmethod
    async def get_capabilities(self) -> dict[str, Any]:
        """Get service capabilities (available layers, CRS, etc.).

        Returns:
            Dictionary with service metadata:
            {
                "title": str,
                "layers": list[str],
                "crs": list[str],
                "formats": list[str],
                "bbox": [minx, miny, maxx, maxy]
            }
        """
        pass

    @abstractmethod
    async def get_features(
        self,
        bbox: tuple[float, float, float, float],
        layers: Optional[list[str]] = None,
        crs: str = "EPSG:4326",
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> gpd.GeoDataFrame:
        """Download vector features within bounding box.

        Args:
            bbox: (minx, miny, maxx, maxy) in specified CRS
            layers: Layer names to download (None = all)
            crs: Coordinate reference system
            limit: Maximum features per layer
            **kwargs: Protocol-specific parameters

        Returns:
            GeoDataFrame with downloaded features
        """
        pass

    @abstractmethod
    async def get_coverage(
        self,
        bbox: tuple[float, float, float, float],
        product: str,
        resolution: int,
        crs: str = "EPSG:4326",
        **kwargs: Any,
    ) -> Any:
        """Download raster coverage within bounding box.

        Args:
            bbox: (minx, miny, maxx, maxy) in specified CRS
            product: Product/layer name
            resolution: Resolution in meters
            crs: Coordinate reference system
            **kwargs: Protocol-specific parameters

        Returns:
            Raster data (format TBD - numpy array, rasterio dataset, etc.)
        """
        pass

    def validate_bbox(self, bbox: tuple[float, float, float, float]) -> None:
        """Validate bounding box coordinates.

        Args:
            bbox: (minx, miny, maxx, maxy)

        Raises:
            ValueError: If bbox is invalid
        """
        minx, miny, maxx, maxy = bbox
        if minx >= maxx:
            raise ValueError(f"Invalid bbox: minx ({minx}) >= maxx ({maxx})")
        if miny >= maxy:
            raise ValueError(f"Invalid bbox: miny ({miny}) >= maxy ({maxy})")

    def bbox_to_geometry(
        self, bbox: tuple[float, float, float, float]
    ) -> box:  # type: ignore
        """Convert bbox to Shapely box geometry.

        Args:
            bbox: (minx, miny, maxx, maxy)

        Returns:
            Shapely Polygon (box)
        """
        return box(*bbox)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client.

        Returns:
            Async HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def __aenter__(self) -> "Protocol":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - cleanup HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
