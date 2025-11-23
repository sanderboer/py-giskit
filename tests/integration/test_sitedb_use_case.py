"""Integration tests for GISKit - Sitedb use case validation.

These tests validate that GISKit can replicate Sitedb's functionality
for downloading Dutch spatial data (BGT, BAG, BRK, etc.) using recipes.

Tests are marked with @pytest.mark.integration and require:
- Internet connection
- Access to PDOK APIs
- Nominatim geocoding service

Run with: pytest tests/integration/test_sitedb_use_case.py -v -m integration
"""

import asyncio
from pathlib import Path

import geopandas as gpd
import pytest

# Import to register providers
import giskit.providers.pdok  # noqa: F401
from giskit.core.geocoding import geocode
from giskit.core.recipe import Dataset, Location, LocationType, Output, Recipe
from giskit.core.spatial import buffer_point_to_bbox, transform_bbox
from giskit.protocols.ogc_features import OGCFeaturesProtocol
from giskit.protocols.quirks import get_quirks
from giskit.protocols.quirks_monitor import get_monitor
from giskit.providers.base import get_provider


@pytest.mark.integration
@pytest.mark.asyncio
class TestSitedbUseCase:
    """Test suite validating GISKit against Sitedb use cases."""

    async def test_geocode_curieweg_address(self):
        """Test geocoding Curieweg 7a, Spijkenisse address."""
        address = "Curieweg 7a, Spijkenisse, Netherlands"

        lon, lat = await geocode(address)

        # Curieweg is in Spijkenisse (near Rotterdam)
        # Approximate coordinates: 51.84°N, 4.33°E
        assert 51.8 < lat < 51.9, f"Latitude {lat} not in expected range"
        assert 4.3 < lon < 4.4, f"Longitude {lon} not in expected range"

        print(f"✓ Geocoded '{address}' to ({lon:.6f}, {lat:.6f})")

    async def test_buffer_curieweg_location(self):
        """Test buffering Curieweg location with 200m radius."""
        # Approximate Curieweg coordinates
        lon, lat = 4.33, 51.84

        # Buffer 200m radius
        bbox = buffer_point_to_bbox(lon, lat, radius_m=200, crs="EPSG:4326")

        minx, miny, maxx, maxy = bbox

        # Bbox should be roughly 400m x 400m (allowing for lat/lon distortion)
        width_deg = maxx - minx
        height_deg = maxy - miny

        # At this latitude, 1 degree ≈ 70km, so 400m ≈ 0.0057 degrees
        # Allow wider range due to projection distortions
        assert 0.003 < width_deg < 0.015, f"Width {width_deg} degrees unexpected"
        assert 0.003 < height_deg < 0.015, f"Height {height_deg} degrees unexpected"

        print(f"✓ Buffered 200m → bbox: {bbox}")

    async def test_transform_curieweg_to_rd_new(self):
        """Test transforming Curieweg bbox from WGS84 to RD New (EPSG:28992)."""
        # WGS84 bbox around Curieweg
        bbox_wgs84 = (4.32, 51.83, 4.34, 51.85)

        # Transform to RD New (Dutch national grid)
        bbox_rd = transform_bbox(bbox_wgs84, "EPSG:4326", "EPSG:28992")

        minx, miny, maxx, maxy = bbox_rd

        # RD New coordinates for Spijkenisse area: roughly (82000, 428000)
        assert 80000 < minx < 90000, f"RD X min {minx} out of range"
        assert 425000 < miny < 435000, f"RD Y min {miny} out of range"
        assert 80000 < maxx < 90000, f"RD X max {maxx} out of range"
        assert 425000 < maxy < 435000, f"RD Y max {maxy} out of range"

        print(f"✓ Transformed WGS84 {bbox_wgs84} → RD New {bbox_rd}")

    @pytest.mark.slow
    async def test_download_bgt_pand_curieweg(self):
        """Test downloading BGT pand (building footprints) for Curieweg area."""
        # Small bbox around Curieweg (WGS84)
        bbox = (4.328, 51.838, 4.332, 51.842)

        # Get PDOK provider
        provider = get_provider("pdok")

        # Create dataset specification
        dataset = Dataset(provider="pdok", service="bgt", layers=["pand"])

        # Create location (using bbox directly)
        location = Location(type=LocationType.BBOX, value=list(bbox), crs="EPSG:4326")

        # Download
        gdf = await provider.download_dataset(
            dataset=dataset,
            location=location,
            output_path=Path("/tmp/test_bgt_pand.gpkg"),
            output_crs="EPSG:28992",
        )

        # Assertions
        assert not gdf.empty, "No features downloaded"
        assert gdf.crs is not None, "CRS not set"
        assert gdf.crs.to_epsg() == 28992, "CRS should be RD New"
        assert "geometry" in gdf.columns, "Missing geometry column"
        assert "_collection" in gdf.columns, "Missing collection metadata"
        assert gdf["_collection"].iloc[0] == "pand", "Wrong collection"

        print(f"✓ Downloaded {len(gdf)} BGT pand features")

    @pytest.mark.slow
    async def test_download_bgt_multiple_layers_curieweg(self):
        """Test downloading multiple BGT layers (pand, wegdeel, waterdeel)."""
        bbox = (4.328, 51.838, 4.332, 51.842)

        provider = get_provider("pdok")
        dataset = Dataset(provider="pdok", service="bgt", layers=["pand", "wegdeel", "waterdeel"])
        location = Location(type=LocationType.BBOX, value=list(bbox), crs="EPSG:4326")

        gdf = await provider.download_dataset(
            dataset=dataset,
            location=location,
            output_path=Path("/tmp/test_bgt_multi.gpkg"),
            output_crs="EPSG:28992",
        )

        # Should have features from multiple collections
        assert not gdf.empty, "No features downloaded"
        collections = gdf["_collection"].unique()

        # At least one of these layers should have data
        expected_collections = {"pand", "wegdeel", "waterdeel"}
        found_collections = set(collections) & expected_collections
        assert len(found_collections) > 0, f"No expected collections found: {collections}"

        print(f"✓ Downloaded {len(gdf)} features from {len(collections)} collections")
        print(f"  Collections: {', '.join(collections)}")

    @pytest.mark.slow
    async def test_full_curieweg_recipe(self):
        """Test complete Curieweg recipe (mirrors Sitedb use case)."""
        # Load the Sitedb Curieweg recipe
        recipe_path = Path("recipes/sitedb_curieweg.json")

        if not recipe_path.exists():
            pytest.skip(f"Recipe not found: {recipe_path}")

        recipe = Recipe.from_file(recipe_path)

        # Validate recipe
        assert recipe.name == "Sitedb Use Case - Curieweg Spijkenisse"
        assert recipe.location.type == LocationType.ADDRESS
        assert recipe.location.radius == 200
        assert len(recipe.datasets) >= 2  # BGT + BAG minimum

        # Get bbox (includes geocoding + buffering)
        bbox = await recipe.get_bbox_wgs84()

        assert len(bbox) == 4, "Bbox should be (minx, miny, maxx, maxy)"
        minx, miny, maxx, maxy = bbox

        # Should be around Spijkenisse
        assert 51.8 < miny < 51.9, f"Bbox min lat {miny} unexpected"
        assert 51.8 < maxy < 51.9, f"Bbox max lat {maxy} unexpected"
        assert 4.3 < minx < 4.4, f"Bbox min lon {minx} unexpected"
        assert 4.3 < maxx < 4.4, f"Bbox max lon {maxx} unexpected"

        print("✓ Recipe validated")
        print(f"  Address: {recipe.location.value}")
        print(f"  Bbox (WGS84): {bbox}")
        print(f"  Datasets: {len(recipe.datasets)}")

    @pytest.mark.slow
    async def test_ogc_features_protocol_directly(self):
        """Test OGC Features protocol against PDOK BGT API directly."""
        protocol = OGCFeaturesProtocol(base_url="https://api.pdok.nl/lv/bgt/ogc/v1_0/")

        # Get capabilities
        async with protocol:
            capabilities = await protocol.get_capabilities()

            assert "layers" in capabilities
            assert "pand" in capabilities["layers"], "pand not in available layers"

            # Download small area
            bbox = (4.328, 51.838, 4.332, 51.842)
            gdf = await protocol.get_features(
                bbox=bbox, layers=["pand"], crs="EPSG:28992", limit=100
            )

            if not gdf.empty:
                assert gdf.crs is not None, "CRS not set"
                assert gdf.crs.to_epsg() == 28992
                print(f"✓ OGC Features protocol works: {len(gdf)} features")
            else:
                print("⚠ No features in test area (acceptable)")

    async def test_recipe_bbox_calculation_all_types(self):
        """Test bbox calculation for all location types."""
        # 1. Bbox type (direct)
        recipe_bbox = Recipe(
            location=Location(type=LocationType.BBOX, value=[4.88, 52.36, 4.92, 52.38]),
            datasets=[Dataset(provider="pdok", service="bgt", layers=["pand"])],
            output=Output(path=Path("/tmp/test.gpkg")),
        )
        bbox = await recipe_bbox.get_bbox_wgs84()
        assert bbox == (4.88, 52.36, 4.92, 52.38)

        # 2. Point type (buffering)
        recipe_point = Recipe(
            location=Location(type=LocationType.POINT, value=[4.9, 52.37], radius=100),
            datasets=[Dataset(provider="pdok", service="bgt", layers=["pand"])],
            output=Output(path=Path("/tmp/test.gpkg")),
        )
        bbox = await recipe_point.get_bbox_wgs84()
        assert len(bbox) == 4
        # Should be small bbox around point
        assert abs(bbox[0] - 4.9) < 0.01
        assert abs(bbox[2] - 4.9) < 0.01

        # 3. Polygon type
        recipe_polygon = Recipe(
            location=Location(
                type=LocationType.POLYGON,
                value=[[4.88, 52.36], [4.92, 52.36], [4.90, 52.38], [4.88, 52.36]],
            ),
            datasets=[Dataset(provider="pdok", service="bgt", layers=["pand"])],
            output=Output(path=Path("/tmp/test.gpkg")),
        )
        bbox = await recipe_polygon.get_bbox_wgs84()
        assert bbox[0] == pytest.approx(4.88, abs=0.01)
        assert bbox[2] == pytest.approx(4.92, abs=0.01)

        print("✓ All location types work correctly")


@pytest.mark.integration
class TestProviderRegistry:
    """Test provider registration and discovery."""

    def test_pdok_provider_registered(self):
        """Test that PDOK provider is registered."""
        from giskit.providers.base import list_providers

        providers = list_providers()
        assert "pdok" in providers, "PDOK provider not registered"

    def test_pdok_provider_metadata(self):
        """Test PDOK provider metadata."""
        provider = get_provider("pdok")
        metadata = asyncio.run(provider.get_metadata())

        assert metadata["name"] == "PDOK"
        assert metadata["coverage"] == "Netherlands"
        assert "bgt" in metadata["services"]
        assert "bag" in metadata["services"]

        print(f"✓ PDOK metadata: {metadata['name']}")
        print(f"  Services: {', '.join(metadata['services'])}")

    def test_pdok_supported_services(self):
        """Test PDOK supported services list."""
        provider = get_provider("pdok")
        services = provider.get_supported_services()

        assert "bgt" in services
        assert "bag" in services

        print(f"✓ PDOK services: {', '.join(services)}")


@pytest.mark.integration
@pytest.mark.slow
class TestSitedbComparison:
    """Tests comparing GISKit output with Sitedb output."""

    async def test_compare_feature_counts(self):
        """Compare feature counts between GISKit and Sitedb for same area.

        NOTE: This test requires running Sitedb download first to generate
        comparison data. Skip if Sitedb database doesn't exist.
        """
        sitedb_db = Path("../Sitedb/data/curieweg-7a-spijkenisse.gpkg")

        if not sitedb_db.exists():
            pytest.skip(f"Sitedb database not found: {sitedb_db}")

        # Read Sitedb BGT pand data
        try:
            sitedb_gdf = gpd.read_file(sitedb_db, layer="bgt_pand")
        except Exception:
            pytest.skip("BGT pand layer not found in Sitedb database")

        # Download same area with GISKit
        bbox = (4.328, 51.838, 4.332, 51.842)
        provider = get_provider("pdok")
        dataset = Dataset(provider="pdok", service="bgt", layers=["pand"])
        location = Location(type=LocationType.BBOX, value=list(bbox), crs="EPSG:4326")

        giskit_gdf = await provider.download_dataset(
            dataset=dataset,
            location=location,
            output_path=Path("/tmp/giskit_test.gpkg"),
            output_crs="EPSG:28992",
        )

        # Compare counts (should be similar, not necessarily exact due to timing)
        sitedb_count = len(sitedb_gdf)
        giskit_count = len(giskit_gdf)

        print("\nFeature count comparison:")
        print(f"  Sitedb:  {sitedb_count}")
        print(f"  GISKit:  {giskit_count}")

        # Allow 10% difference due to API timing/updates
        assert (
            abs(sitedb_count - giskit_count) / max(sitedb_count, 1) < 0.1
        ), "Feature counts differ by more than 10%"


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuirksIntegration:
    """Test that quirks are properly applied during real API operations."""

    async def test_pdok_quirks_are_configured(self):
        """Test that PDOK quirks are properly configured."""
        # Get PDOK quirks
        quirks = get_quirks("pdok", "ogc-features")

        # Verify PDOK quirks are configured as expected
        assert quirks.requires_trailing_slash is True, "PDOK requires trailing slash"
        assert quirks.require_format_param is True, "PDOK requires format parameter"
        assert quirks.format_param_name == "f", "PDOK uses 'f' parameter"
        assert quirks.format_param_value == "json", "PDOK requires 'json' value"

        # Verify quirks are applied to URLs
        protocol = OGCFeaturesProtocol(
            base_url="https://api.pdok.nl/lv/bgt/ogc/v1_0", quirks=quirks
        )
        assert protocol.base_url.endswith("/"), "URL should have trailing slash"

        # Verify quirks are applied to params
        params = {}
        params_with_quirks = quirks.apply_to_params(params)
        assert params_with_quirks["f"] == "json", "Should add format parameter"

        print("\n✓ PDOK quirks configuration verified")

    async def test_quirks_correctly_fix_pdok_urls(self):
        """Test that quirks correctly fix PDOK URL construction."""
        # Get PDOK quirks
        quirks = get_quirks("pdok", "ogc-features")

        # Verify quirks are configured correctly
        assert quirks.requires_trailing_slash is True
        assert quirks.require_format_param is True
        assert quirks.format_param_name == "f"
        assert quirks.format_param_value == "json"

        # Create protocol with quirks (use service root URL, not collection-specific)
        protocol = OGCFeaturesProtocol(
            base_url="https://api.pdok.nl/lv/bgt/ogc/v1_0", quirks=quirks
        )

        # Verify URL was constructed with trailing slash
        assert protocol.base_url.endswith("/")

        # Make a simple capabilities request
        try:
            capabilities = await protocol.get_capabilities()
            assert capabilities is not None
            assert "layers" in capabilities
            print(f"\n✓ Successfully fetched {len(capabilities['layers'])} layers using quirks")
        except Exception as e:
            pytest.fail(f"Failed to fetch capabilities with quirks: {e}")

    async def test_monitor_tracks_multiple_providers(self):
        """Test that monitor can track quirks from multiple providers."""
        monitor = get_monitor()
        monitor.reset()

        # Apply quirks for PDOK
        monitor.record_quirk_applied("pdok", "ogc-features", "format_param")
        monitor.record_quirk_applied("pdok", "ogc-features", "trailing_slash")

        # Simulate another provider (even if we don't have one yet)
        monitor.record_quirk_applied("test-provider", "test-protocol", "custom_timeout")

        # Get statistics
        stats = monitor.get_statistics()

        # Should have both providers
        assert "pdok" in stats
        assert "test-provider" in stats

        # Get most used quirks
        most_used = monitor.get_most_used_quirks(limit=5)
        assert len(most_used) == 3

        print("\n✓ Monitor tracks multiple providers:")
        for usage in most_used:
            print(f"  {usage.provider}/{usage.protocol}/{usage.quirk_type}: {usage.applied_count}x")


# Utility function for running async tests in sync context
def run_async_test(coro):
    """Helper to run async tests synchronously."""
    return asyncio.run(coro)


if __name__ == "__main__":
    # Run tests directly
    print("Running GISKit Integration Tests - Sitedb Use Case\n")
    print("=" * 60)

    test_suite = TestSitedbUseCase()

    print("\n1. Testing geocoding...")
    run_async_test(test_suite.test_geocode_curieweg_address())

    print("\n2. Testing buffering...")
    run_async_test(test_suite.test_buffer_curieweg_location())

    print("\n3. Testing CRS transformation...")
    run_async_test(test_suite.test_transform_curieweg_to_rd_new())

    print("\n4. Testing recipe bbox calculation...")
    run_async_test(test_suite.test_recipe_bbox_calculation_all_types())

    print("\n" + "=" * 60)
    print("✓ All basic tests passed!")
    print("\nRun full test suite with: pytest tests/integration/test_sitedb_use_case.py -v")
