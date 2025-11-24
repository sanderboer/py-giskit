#!/usr/bin/env python3
"""Demo script showing how to use the service catalog to discover data sources.

The catalog makes it easy to:
1. Browse available providers and services
2. Search for specific types of data
3. Filter by protocol or category
4. Find the right service IDs to use in recipes
"""

from giskit.catalog import (
    list_all_services,
    list_services_by_category,
    list_services_by_protocol,
    print_catalog,
    search_services,
)


def demo_overview():
    """Show catalog overview."""
    print("\n" + "=" * 80)
    print("1. CATALOG OVERVIEW")
    print("=" * 80)
    print_catalog()


def demo_search():
    """Demonstrate search functionality."""
    print("\n" + "=" * 80)
    print("2. SEARCH EXAMPLES")
    print("=" * 80)

    # Search for elevation data
    print("\n🔍 Searching for 'elevation' data:")
    results = search_services("elevation")
    for provider, services in results.items():
        for svc in services:
            print(f"  {provider}/{svc['id']}: {svc['title']}")

    # Search for 3D data
    print("\n🔍 Searching for '3d' data:")
    results = search_services("3d")
    for provider, services in results.items():
        for svc in services:
            print(f"  {provider}/{svc['id']}: {svc['title']}")

    # Search for cadastral data
    print("\n🔍 Searching for 'cadastral' data:")
    results = search_services("kadaster")
    for provider, services in results.items():
        for svc in services:
            print(f"  {provider}/{svc['id']}: {svc['title']}")


def demo_by_protocol():
    """Show services grouped by protocol."""
    print("\n" + "=" * 80)
    print("3. SERVICES BY PROTOCOL")
    print("=" * 80)

    # OGC Features (vector data)
    print("\n📊 OGC Features (vector data):")
    ogc = list_services_by_protocol("ogc-features")
    for provider, services in ogc.items():
        print(f"  {provider}: {len(services)} services")

    # WCS (raster/elevation data)
    print("\n🗺️  WCS (raster/elevation data):")
    wcs = list_services_by_protocol("wcs")
    for provider, services in wcs.items():
        print(f"  {provider}: {services}")

    # WMTS (tile services)
    print("\n🖼️  WMTS (pre-rendered tiles):")
    wmts = list_services_by_protocol("wmts")
    for provider, services in wmts.items():
        print(f"  {provider}: {services}")


def demo_by_category():
    """Show services grouped by category."""
    print("\n" + "=" * 80)
    print("4. SERVICES BY CATEGORY")
    print("=" * 80)

    by_category = list_services_by_category()

    for provider, categories in by_category.items():
        print(f"\n{provider.upper()}:")
        for category, services in sorted(categories.items()):
            service_list = ", ".join(services[:3])
            more = f" (+{len(services)-3} more)" if len(services) > 3 else ""
            print(f"  {category:20} → {service_list}{more}")


def demo_detailed_info():
    """Show detailed service information."""
    print("\n" + "=" * 80)
    print("5. DETAILED SERVICE INFO")
    print("=" * 80)

    # Get detailed catalog
    catalog = list_all_services(detailed=True)

    # Show details for PDOK's BGT service
    pdok_services = catalog["pdok"]["services"]
    bgt = pdok_services.get("bgt", {})

    print("\n📋 BGT (Basisregistratie Grootschalige Topografie):")
    print(f"  Title: {bgt.get('title', 'N/A')}")
    print(f"  Protocol: {bgt.get('protocol', 'N/A')}")
    print(f"  Category: {bgt.get('category', 'N/A')}")
    print(f"  URL: {bgt.get('url', 'N/A')}")
    print(f"  Description: {bgt.get('description', 'N/A')}")


def demo_recipe_composition():
    """Show how to use catalog results in recipes."""
    print("\n" + "=" * 80)
    print("6. COMPOSING A RECIPE")
    print("=" * 80)

    print("\nScenario: I want elevation data and building footprints\n")

    # Step 1: Find elevation data
    print("Step 1: Search for elevation data")
    elevation = search_services("elevation")
    for provider, services in elevation.items():
        for svc in services:
            print(f"  Found: {provider}/{svc['id']} - {svc['title']}")

    # Step 2: Find building data
    print("\nStep 2: Search for building data")
    buildings = search_services("building")
    for provider, services in buildings.items():
        for svc in services:
            print(f"  Found: {provider}/{svc['id']} - {svc['title']}")

    # Step 3: Show example recipe
    print("\nStep 3: Compose recipe:")
    print(
        """
{
  "name": "Elevation and Buildings",
  "location": {
    "bbox": [5.0, 52.0, 5.1, 52.1]
  },
  "datasets": [
    {
      "provider": "pdok",
      "service": "ahn",
      "layers": ["dsm"]
    },
    {
      "provider": "pdok",
      "service": "bag",
      "layers": ["pand"]
    }
  ]
}
"""
    )


if __name__ == "__main__":
    print("=" * 80)
    print("GISKIT CATALOG DEMO")
    print("=" * 80)
    print("This demo shows how to discover and explore available data sources")

    demo_overview()
    demo_search()
    demo_by_protocol()
    demo_by_category()
    demo_detailed_info()
    demo_recipe_composition()

    print("\n" + "=" * 80)
    print("Demo complete! 🎉")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Run 'python -c \"from giskit.catalog import print_catalog; print_catalog()\"'")
    print('  2. Try: search_services("your_keyword")')
    print("  3. Create recipes using the service IDs you discovered")
    print()
