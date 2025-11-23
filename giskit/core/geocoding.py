"""Geocoding utilities using Nominatim (OpenStreetMap)."""

from typing import Optional, Tuple

import httpx


class GeocodingError(Exception):
    """Raised when geocoding fails."""

    pass


class Geocoder:
    """Geocode addresses to coordinates using Nominatim."""

    def __init__(
        self,
        user_agent: str = "giskit/0.1.0",
        base_url: str = "https://nominatim.openstreetmap.org",
    ):
        """Initialize geocoder.

        Args:
            user_agent: User agent for Nominatim requests (required by OSM policy)
            base_url: Nominatim API base URL
        """
        self.user_agent = user_agent
        self.base_url = base_url

    async def geocode(self, address: str, timeout: float = 10.0) -> Tuple[float, float]:
        """Geocode an address to WGS84 coordinates.

        Args:
            address: Address string (e.g., "Dam 1, Amsterdam, Netherlands")
            timeout: Request timeout in seconds

        Returns:
            Tuple of (longitude, latitude) in EPSG:4326

        Raises:
            GeocodingError: If geocoding fails or no results found
        """
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
        }

        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise GeocodingError(f"Geocoding request failed: {e}") from e

            results = response.json()

            if not results:
                raise GeocodingError(f"No results found for address: {address}")

            # Nominatim returns lat, lon - we need lon, lat
            result = results[0]
            lat = float(result["lat"])
            lon = float(result["lon"])

            return (lon, lat)

    async def reverse_geocode(self, lon: float, lat: float, timeout: float = 10.0) -> str:
        """Reverse geocode coordinates to an address.

        Args:
            lon: Longitude in EPSG:4326
            lat: Latitude in EPSG:4326
            timeout: Request timeout in seconds

        Returns:
            Address string

        Raises:
            GeocodingError: If reverse geocoding fails
        """
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
        }

        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/reverse",
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise GeocodingError(f"Reverse geocoding failed: {e}") from e

            result = response.json()

            if "error" in result:
                raise GeocodingError(f"Reverse geocoding error: {result['error']}")

            return result.get("display_name", f"{lat}, {lon}")


# Global geocoder instance
_geocoder: Optional[Geocoder] = None


def get_geocoder() -> Geocoder:
    """Get the global geocoder instance.

    Returns:
        Geocoder instance
    """
    global _geocoder
    if _geocoder is None:
        _geocoder = Geocoder()
    return _geocoder


async def geocode(address: str) -> Tuple[float, float]:
    """Geocode an address to WGS84 coordinates.

    Args:
        address: Address string

    Returns:
        Tuple of (longitude, latitude) in EPSG:4326
    """
    geocoder = get_geocoder()
    return await geocoder.geocode(address)


async def reverse_geocode(lon: float, lat: float) -> str:
    """Reverse geocode coordinates to an address.

    Args:
        lon: Longitude in EPSG:4326
        lat: Latitude in EPSG:4326

    Returns:
        Address string
    """
    geocoder = get_geocoder()
    return await geocoder.reverse_geocode(lon, lat)
