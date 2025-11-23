"""API Quirks configuration and handling.

This module defines common API quirks and how to handle them.
Quirks are provider-specific deviations from standard protocols.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from giskit.config import load_quirks


class ProtocolQuirks(BaseModel):
    """Configuration for protocol-specific quirks.

    Quirks are deviations from standard protocol behavior that
    require special handling for specific providers.

    Examples:
        PDOK requires ?f=json parameter:
            quirks = ProtocolQuirks(
                require_format_param=True,
                format_param_name="f",
                format_param_value="json"
            )

        Provider with trailing slash requirement:
            quirks = ProtocolQuirks(requires_trailing_slash=True)
    """

    # URL Construction Quirks
    requires_trailing_slash: bool = Field(
        False, description="Add trailing slash to base URL to prevent urljoin() issues"
    )

    # Request Parameter Quirks
    require_format_param: bool = Field(
        False, description="Require explicit format parameter in requests"
    )
    format_param_name: str = Field(
        "f", description="Name of format parameter (e.g., 'f', 'format', 'outputFormat')"
    )
    format_param_value: str = Field(
        "json",
        description="Value for format parameter (e.g., 'json', 'geojson', 'application/json')",
    )

    # Pagination Quirks
    max_features_limit: Optional[int] = Field(
        None, description="Maximum features per request (if API ignores limit parameter)"
    )
    pagination_broken: bool = Field(False, description="API pagination doesn't work correctly")

    # Timeout Quirks
    custom_timeout: Optional[float] = Field(
        None, description="Custom timeout for slow APIs (seconds)"
    )

    # CRS Quirks
    force_crs_in_query: bool = Field(
        False, description="Force CRS parameter in query even if not needed"
    )
    bbox_crs: Optional[str] = Field(
        None,
        description="CRS for bbox parameter (if different from EPSG:4326). E.g., 'EPSG:28992' for BAG3D",
    )

    # Header Quirks
    custom_headers: dict[str, str] = Field(
        default_factory=dict, description="Custom HTTP headers required by API"
    )

    # Response Quirks
    empty_collections_return_404: bool = Field(
        False, description="API returns 404 instead of empty collection"
    )

    # CityJSON Format Quirks (for 3D data like BAG3D)
    format_is_cityjson: bool = Field(
        False, description="Response is CityJSON format instead of GeoJSON"
    )
    cityjson_version: Optional[str] = Field(
        None, description="CityJSON version (e.g., '1.1', '2.0')"
    )
    has_per_page_transform: bool = Field(
        False,
        description="CRITICAL: Each pagination page has different transform (scale/translate)",
    )
    transform_applies_to_vertices: bool = Field(
        False,
        description="Vertices are integers that need transform: real = vertex * scale + translate",
    )
    vertices_are_integers: bool = Field(
        False, description="Vertex coordinates stored as integers requiring scaling"
    )
    has_lod_hierarchy: bool = Field(
        False, description="Geometry has LOD (Level of Detail) hierarchy"
    )
    geometry_in_city_objects: bool = Field(
        False, description="Geometry stored in CityObjects structure, not standard GeoJSON"
    )

    # Metadata
    description: Optional[str] = Field(
        None, description="Human-readable description of why these quirks are needed"
    )
    issue_url: Optional[str] = Field(None, description="Link to issue tracker or documentation")
    workaround_date: Optional[str] = Field(
        None, description="Date when workaround was added (YYYY-MM-DD)"
    )

    def apply_to_url(self, url: str) -> str:
        """Apply URL quirks to base URL.

        Args:
            url: Base URL

        Returns:
            Modified URL with quirks applied
        """
        if self.requires_trailing_slash and not url.endswith("/"):
            return url + "/"
        return url

    def apply_to_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply parameter quirks to request params.

        Args:
            params: Request parameters

        Returns:
            Modified parameters with quirks applied
        """
        params = params.copy()

        # Add format parameter if required
        if self.require_format_param:
            params[self.format_param_name] = self.format_param_value

        # Override limit if max is set
        if self.max_features_limit and "limit" in params:
            params["limit"] = min(params["limit"], self.max_features_limit)

        return params

    def apply_to_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Apply header quirks.

        Args:
            headers: Request headers

        Returns:
            Modified headers with quirks applied
        """
        headers = headers.copy()
        headers.update(self.custom_headers)
        return headers

    def get_timeout(self, default: float) -> float:
        """Get timeout with quirk applied.

        Args:
            default: Default timeout

        Returns:
            Timeout to use (custom or default)
        """
        return self.custom_timeout if self.custom_timeout else default


# Known quirks for common providers and formats
# This is the legacy/fallback configuration - prefer loading from config/quirks/*.yml
LEGACY_KNOWN_QUIRKS: dict[str, dict[str, ProtocolQuirks]] = {
    # Provider-specific protocol quirks
    "pdok": {
        "ogc-features": ProtocolQuirks(
            requires_trailing_slash=True,
            require_format_param=True,
            format_param_name="f",
            format_param_value="json",
            description="PDOK OGC API requires ?f=json and trailing slash in base URL",
            issue_url="https://github.com/PDOK/issues/ogc-features-format-param",
            workaround_date="2024-11-22",
        )
    },
    # Format-specific quirks (apply to any service using this format)
    "cityjson": {
        "format": ProtocolQuirks(
            # CityJSON format quirks
            format_is_cityjson=True,
            cityjson_version="2.0",
            geometry_in_city_objects=True,
            has_lod_hierarchy=True,
            # CRITICAL: Transform quirks (affects ALL CityJSON sources)
            has_per_page_transform=True,
            transform_applies_to_vertices=True,
            vertices_are_integers=True,
            # Performance params
            custom_timeout=60.0,  # 3D data can be slow
            description=(
                "CityJSON 2.0 format uses per-page transforms for vertex compression. "
                "CRITICAL: Each pagination page has its own transform (scale/translate). "
                "Vertices are integers that must be scaled: real_coord = vertex * scale + translate. "
                "Applying wrong transform to features causes coordinate errors! "
                "This affects: BAG3D, 3D-basisvoorziening, and other 3D services."
            ),
            issue_url="https://www.cityjson.org/specs/2.0.0/#transform-object",
            workaround_date="2024-11-22",
        )
    },
    # Service-specific quirks (inherits format quirks)
    "bag3d": {
        "ogc-features": ProtocolQuirks(
            # Inherits CityJSON format quirks
            format_is_cityjson=True,
            cityjson_version="2.0",
            geometry_in_city_objects=True,
            has_lod_hierarchy=True,
            has_per_page_transform=True,
            transform_applies_to_vertices=True,
            vertices_are_integers=True,
            custom_timeout=60.0,
            description="BAG3D uses CityJSON 2.0 format (see 'cityjson' format quirks)",
            issue_url="https://api.3dbag.nl/api.html",
            workaround_date="2024-11-22",
        )
    },
    # Add more providers/formats as discovered
    # "other-provider": {
    #     "ogc-features": ProtocolQuirks(...)
    # }
}

# Load quirks from config with fallback to legacy hardcoded quirks
# This allows users to customize quirks via YAML config files
from giskit.config import load_quirks

KNOWN_QUIRKS = load_quirks(fallback=LEGACY_KNOWN_QUIRKS)


def get_quirks(provider: str, protocol: str) -> ProtocolQuirks:
    """Get known quirks for a provider/protocol combination.

    Args:
        provider: Provider name (e.g., "pdok", "bag3d") or format name (e.g., "cityjson")
        protocol: Protocol name (e.g., "ogc-features", "format")

    Returns:
        ProtocolQuirks instance (default quirks if unknown)

    Examples:
        >>> # Provider quirks
        >>> quirks = get_quirks("pdok", "ogc-features")
        >>> quirks.requires_trailing_slash
        True
        >>> quirks.require_format_param
        True

        >>> # Format quirks
        >>> quirks = get_quirks("cityjson", "format")
        >>> quirks.has_per_page_transform
        True
        >>> quirks.format_is_cityjson
        True
    """
    return KNOWN_QUIRKS.get(provider, {}).get(protocol, ProtocolQuirks())


def get_format_quirks(format_name: str) -> ProtocolQuirks:
    """Get quirks for a specific data format.

    This is a convenience wrapper for getting format-specific quirks.

    Args:
        format_name: Format name (e.g., "cityjson")

    Returns:
        ProtocolQuirks instance for the format

    Examples:
        >>> quirks = get_format_quirks("cityjson")
        >>> quirks.has_per_page_transform
        True
    """
    return get_quirks(format_name, "format")


def get_service_quirks(provider: str, protocol: str, service: str) -> ProtocolQuirks:
    """Get quirks for a specific service within a provider.

    This allows service-specific quirks to override provider-level quirks.
    For example, BAG3D within PDOK needs bbox_crs="EPSG:28992".

    Args:
        provider: Provider name (e.g., "pdok")
        protocol: Protocol name (e.g., "ogc-features")
        service: Service name (e.g., "bag3d", "bgt")

    Returns:
        ProtocolQuirks instance (merges provider and service quirks)

    Examples:
        >>> quirks = get_service_quirks("pdok", "ogc-features", "bag3d")
        >>> quirks.bbox_crs
        'EPSG:28992'
    """
    # Start with provider-level quirks
    base_quirks = get_quirks(provider, protocol)

    # Check if there are service-specific quirks
    service_key = f"{provider}-{service}"
    if service_key in KNOWN_QUIRKS and protocol in KNOWN_QUIRKS[service_key]:
        # Merge service quirks over base quirks
        service_quirks_dict = KNOWN_QUIRKS[service_key][protocol]
        base_dict = base_quirks.model_dump()
        base_dict.update(service_quirks_dict.model_dump(exclude_unset=True))
        return ProtocolQuirks(**base_dict)

    # Check if service has its own quirks (for external services like bag3d)
    if service in KNOWN_QUIRKS and protocol in KNOWN_QUIRKS[service]:
        # Use service quirks directly
        service_quirks_dict = KNOWN_QUIRKS[service][protocol]
        base_dict = base_quirks.model_dump()
        base_dict.update(service_quirks_dict.model_dump(exclude_unset=True))
        return ProtocolQuirks(**base_dict)

    return base_quirks
