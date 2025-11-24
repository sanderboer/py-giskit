"""Service catalog for discovering available providers and services.

This module provides user-friendly functions to explore what data is available,
making it easy to compose recipes.
"""

from typing import Any, cast

from giskit.providers.base import Provider, get_provider, list_providers


def list_all_services(detailed: bool = False) -> dict[str, Any]:
    """Get a catalog of all available providers and their services.

    This is the main discovery function for users to find what data is available.

    Args:
        detailed: If True, include full service metadata. If False, just list names.

    Returns:
        Dictionary mapping provider names to their services:
        {
            "pdok": {
                "title": "PDOK - Publieke Dienstverlening Op de Kaart",
                "service_count": 52,
                "protocols": ["ogc-features", "wcs", "wmts"],
                "services": {
                    "bgt": {...},
                    "bag": {...},
                    ...
                }
            },
            "bag3d": {...}
        }

    Example:
        >>> from giskit.catalog import list_all_services
        >>>
        >>> # Quick overview
        >>> catalog = list_all_services()
        >>> for provider, info in catalog.items():
        ...     print(f"{provider}: {info['service_count']} services")
        >>>
        >>> # Detailed info
        >>> catalog = list_all_services(detailed=True)
        >>> pdok_services = catalog['pdok']['services']
        >>> print(pdok_services['bgt']['title'])
    """
    catalog = {}

    for provider_name in sorted(list_providers()):
        try:
            provider = get_provider(provider_name)

            # Get provider metadata
            services = provider.get_supported_services()
            protocols = (
                provider.get_supported_protocols()
                if hasattr(provider, "get_supported_protocols")
                else ["unknown"]
            )

            provider_info = {
                "title": getattr(provider, "metadata", {}).get("title", provider_name),
                "service_count": len(services),
                "protocols": protocols,
            }

            # Add services info
            if detailed:
                services_dict = {}
                for service_id in services:
                    try:
                        services_dict[service_id] = provider.get_service_info(service_id)
                    except Exception:
                        services_dict[service_id] = {"error": "Could not load service info"}
                provider_info["services"] = services_dict
            else:
                provider_info["services"] = services

            catalog[provider_name] = provider_info

        except Exception as e:
            catalog[provider_name] = {
                "error": str(e),
                "service_count": 0,
                "protocols": [],
                "services": [],
            }

    return catalog


def search_services(
    query: str, search_in: list[str] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Search for services across all providers.

    Searches in service titles, descriptions, and keywords.

    Args:
        query: Search term (case-insensitive)
        search_in: Fields to search in (default: ['title', 'description', 'keywords'])

    Returns:
        Dictionary mapping provider names to matching services:
        {
            "pdok": [
                {"id": "bgt", "title": "...", "url": "...", "relevance": 0.95},
                ...
            ]
        }

    Example:
        >>> from giskit.catalog import search_services
        >>>
        >>> # Find elevation data
        >>> results = search_services("elevation")
        >>> for provider, services in results.items():
        ...     for svc in services:
        ...         print(f"{provider}/{svc['id']}: {svc['title']}")
        >>>
        >>> # Find 3D data
        >>> results = search_services("3d")
    """
    if search_in is None:
        search_in = ["title", "description", "keywords"]

    query_lower = query.lower().strip()

    # Empty query returns nothing
    if not query_lower:
        return {}

    results = {}

    for provider_name in list_providers():
        try:
            provider = get_provider(provider_name)
            matches = []

            for service_id in provider.get_supported_services():
                try:
                    service_info = provider.get_service_info(service_id)

                    # Check if query matches
                    relevance = 0.0
                    match_count = 0

                    for field in search_in:
                        if field not in service_info:
                            continue

                        value = service_info[field]

                        # Handle different field types
                        if isinstance(value, str):
                            if query_lower in value.lower():
                                match_count += 1
                                # Title matches are most relevant
                                relevance += 1.0 if field == "title" else 0.5

                        elif isinstance(value, list):
                            # Keywords
                            for item in value:
                                if isinstance(item, str) and query_lower in item.lower():
                                    match_count += 1
                                    relevance += 0.3

                    if match_count > 0:
                        matches.append(
                            {
                                "id": service_id,
                                "title": service_info.get("title", service_id),
                                "url": service_info.get("url", ""),
                                "category": service_info.get("category", "unknown"),
                                "protocol": service_info.get("protocol", "unknown"),
                                "relevance": min(relevance, 1.0),
                                "matches": match_count,
                            }
                        )

                except Exception:
                    continue

            if matches:
                # Sort by relevance
                matches.sort(key=lambda x: (-x["relevance"], -x["matches"], x["id"]))
                results[provider_name] = matches

        except Exception:
            continue

    return results


def list_services_by_category(category: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """List services grouped by category.

    Args:
        category: Specific category to filter by (optional)

    Returns:
        Dictionary mapping providers to their services with full metadata:
        {
            "pdok": [
                {"id": "bgt", "title": "...", "category": "base_registers", ...},
                {"id": "bag", "title": "...", "category": "base_registers", ...},
                ...
            ]
        }

    Example:
        >>> from giskit.catalog import list_services_by_category
        >>>
        >>> # Get all categories
        >>> by_category = list_services_by_category()
        >>>
        >>> # Get only elevation data
        >>> elevation = list_services_by_category("elevation")
    """
    result = {}

    for provider_name in list_providers():
        try:
            provider = get_provider(provider_name)

            # Get all categories from provider
            categories = provider.list_categories()

            provider_services = []

            for cat in categories:
                # Skip if filtering by category
                if category and cat != category:
                    continue

                # Get services for this category
                service_ids = provider.get_services_by_category(cat)

                # Get full metadata for each service
                for service_id in service_ids:
                    try:
                        service_info = provider.get_service_info(service_id)
                        provider_services.append(
                            {
                                "id": service_id,
                                "title": service_info.get("title", service_id),
                                "category": service_info.get("category", cat),
                                "protocol": service_info.get("protocol", "unknown"),
                                "url": service_info.get("url", ""),
                            }
                        )
                    except Exception:
                        continue

            if provider_services:
                result[provider_name] = provider_services

        except Exception:
            continue

    return result


def list_services_by_protocol(protocol: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """List services by protocol type.

    Args:
        protocol: Specific protocol to filter by (optional, case-insensitive)
            Options: "ogc-features", "wcs", "wmts", "wfs"

    Returns:
        Dictionary mapping providers to their services with full metadata:
        {
            "pdok": [
                {"id": "bgt", "title": "...", "protocol": "ogc-features", ...},
                {"id": "bag", "title": "...", "protocol": "ogc-features", ...},
                ...
            ]
        }

    Example:
        >>> from giskit.catalog import list_services_by_protocol
        >>>
        >>> # Get all WCS (raster) services
        >>> wcs_services = list_services_by_protocol("wcs")
        >>>
        >>> # Get all WMTS (tile) services
        >>> wmts_services = list_services_by_protocol("wmts")
    """
    result = {}

    # Normalize protocol to lowercase for case-insensitive matching
    protocol_lower = protocol.lower() if protocol else None

    for provider_name in list_providers():
        try:
            provider = get_provider(provider_name)

            provider_services = []

            if hasattr(provider, "get_services_by_protocol") and protocol_lower:
                # Multi-protocol provider
                service_ids = provider.get_services_by_protocol(protocol_lower)
            else:
                # Get all services
                service_ids = provider.get_supported_services()

            # Get full metadata for each service
            for service_id in service_ids:
                try:
                    info = provider.get_service_info(service_id)

                    # Filter by protocol if specified (case-insensitive)
                    if protocol_lower:
                        service_protocol = info.get("protocol", "").lower()
                        if service_protocol != protocol_lower:
                            continue

                    provider_services.append(
                        {
                            "id": service_id,
                            "title": info.get("title", service_id),
                            "protocol": info.get("protocol", "unknown"),
                            "category": info.get("category", "unknown"),
                            "url": info.get("url", ""),
                        }
                    )
                except Exception:
                    continue

            if provider_services:
                result[provider_name] = provider_services

        except Exception:
            continue

    return result


def print_catalog(detailed: bool = False) -> None:
    """Print a formatted catalog of all available services.

    Useful for interactive exploration in a Python REPL or Jupyter notebook.

    Args:
        detailed: Show detailed service information

    Example:
        >>> from giskit.catalog import print_catalog
        >>> print_catalog()
    """
    catalog = list_all_services(detailed=detailed)

    print("=" * 80)
    print("GISKIT SERVICE CATALOG")
    print("=" * 80)
    print()

    for provider_name, provider_info in catalog.items():
        print(f"📦 {provider_name.upper()}")
        print(f"   {provider_info.get('title', '')}")
        print(f"   Services: {provider_info['service_count']}")
        print(f"   Protocols: {', '.join(provider_info['protocols'])}")

        if detailed and "services" in provider_info and isinstance(provider_info["services"], dict):
            print()
            print("   Services:")
            for service_id, service_info in list(provider_info["services"].items())[:10]:
                protocol = service_info.get("protocol", "?")
                title = service_info.get("title", service_id)
                print(f"     • {service_id:30} [{protocol:15}] {title}")

            remaining = provider_info["service_count"] - 10
            if remaining > 0:
                print(f"     ... and {remaining} more")

        print()

    print("=" * 80)
    print(f"Total: {len(catalog)} providers")
    print()
    print("Usage:")
    print("  from giskit.catalog import search_services")
    print("  results = search_services('elevation')")
    print()


def export_catalog_json(
    output_path: str | None = None, detailed: bool = True, pretty: bool = True
) -> str:
    """Export the catalog as JSON.

    Useful for:
    - External tools and integrations
    - Web applications
    - Generating documentation
    - Caching catalog data

    Args:
        output_path: Optional file path to write JSON to. If None, returns JSON string.
        detailed: Include full service metadata (default: True)
        pretty: Pretty-print with indentation (default: True)

    Returns:
        JSON string of the catalog

    Example:
        >>> from giskit.catalog import export_catalog_json
        >>>
        >>> # Get JSON string
        >>> json_str = export_catalog_json()
        >>>
        >>> # Save to file
        >>> export_catalog_json("catalog.json")
        >>>
        >>> # Compact JSON
        >>> json_str = export_catalog_json(pretty=False)
    """
    import json
    from datetime import datetime, timezone
    from pathlib import Path

    catalog = list_all_services(detailed=detailed)

    # Wrap in metadata structure
    export_data = {
        "providers": catalog,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Convert to JSON
    indent = 2 if pretty else None
    json_str = json.dumps(export_data, indent=indent, ensure_ascii=False)

    # Write to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json_str, encoding="utf-8")

    return json_str


__all__ = [
    "list_all_services",
    "search_services",
    "list_services_by_category",
    "list_services_by_protocol",
    "print_catalog",
    "export_catalog_json",
]
