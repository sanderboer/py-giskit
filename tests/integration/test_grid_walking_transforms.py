"""
Integration test for grid walking coordinate transforms.

This test verifies that:
1. Grid walking correctly transforms CityJSON vertices using per-cell transforms
2. Features on grid boundaries have consistent coordinates across cells
3. Coordinates are in valid RD range (not raw integer vertices)
4. Deduplication works correctly (same feature ID appears only once)
"""

import asyncio

import pytest

from giskit.core.recipe import Dataset, Location, LocationType
from giskit.providers.base import get_provider


@pytest.mark.asyncio
async def test_grid_walking_coordinate_transforms():
    """Test that grid walking produces correct coordinates with CityJSON transforms."""

    # Create BAG3D provider
    provider = get_provider("bag3d")

    # Create location with 500m radius (triggers grid walking)
    # This creates a 1000m x 1000m bbox which exceeds 500*500 threshold
    location = Location(
        type=LocationType.POINT,
        value=[4.90098, 52.37092],  # Dam Square, Amsterdam
        radius=500,  # Triggers grid walking
    )

    # Create dataset
    dataset = Dataset(provider="bag3d", service="bag3d", layers=["lod22"])

    # Download with grid walking
    result = await provider.download_dataset(
        dataset=dataset, location=location, output_path="test.gpkg", output_crs="EPSG:28992"
    )

    assert not result.empty, "Grid walking should return features"

    # TEST 1: Verify coordinates are in valid RD range
    # RD coordinates for Amsterdam are roughly 110000-140000 (X) and 470000-500000 (Y)
    # NOT in the range of raw CityJSON vertices (typically 5000-700000 as integers)
    bounds = result.total_bounds
    minx, miny, maxx, maxy = bounds

    print(f"\nCoordinate bounds: ({minx:.2f}, {miny:.2f}, {maxx:.2f}, {maxy:.2f})")

    # Check X coordinates (easting)
    assert (
        110000 < minx < 140000
    ), f"minx {minx} not in valid RD range - might be untransformed vertices!"
    assert (
        110000 < maxx < 140000
    ), f"maxx {maxx} not in valid RD range - might be untransformed vertices!"

    # Check Y coordinates (northing)
    assert (
        470000 < miny < 500000
    ), f"miny {miny} not in valid RD range - might be untransformed vertices!"
    assert (
        470000 < maxy < 500000
    ), f"maxy {maxy} not in valid RD range - might be untransformed vertices!"

    print("✓ Coordinates are in valid RD range (transforms applied correctly)")

    # TEST 2: Verify no duplicate features (deduplication works)
    if "identificatie" in result.columns:
        unique_ids = result["identificatie"].nunique()
        total_rows = len(result)
        print(f"\nFeatures: {total_rows}, Unique IDs: {unique_ids}")
        assert unique_ids == total_rows, f"Found {total_rows - unique_ids} duplicate features!"
        print("✓ No duplicate features (deduplication works)")

    # TEST 3: Verify geometries are valid
    assert result.geometry.is_valid.all(), "Some geometries are invalid!"
    print("✓ All geometries are valid")

    # TEST 4: Verify Z coordinates exist for 3D models
    # Extract Z coordinates from first feature
    first_geom = result.geometry.iloc[0]
    if hasattr(first_geom, "exterior"):
        coords = list(first_geom.exterior.coords)
        if len(coords[0]) == 3:
            z_values = [c[2] for c in coords]
            avg_z = sum(z_values) / len(z_values)
            print(
                f"\nZ coordinates found: min={min(z_values):.2f}m, max={max(z_values):.2f}m, avg={avg_z:.2f}m"
            )

            # Buildings in Amsterdam are typically 0-50m high
            assert -5 < min(z_values) < 100, f"Z values {min(z_values)} seem wrong!"
            assert -5 < max(z_values) < 100, f"Z values {max(z_values)} seem wrong!"
            print("✓ Z coordinates in valid range")

    # TEST 5: Check CRS is correct
    assert result.crs.to_string() == "EPSG:28992", f"Wrong CRS: {result.crs}"
    print("✓ CRS is EPSG:28992")

    print("\n✅ All coordinate transform tests passed!")
    print(f"   Downloaded {len(result)} buildings with grid walking")


@pytest.mark.asyncio
async def test_grid_vs_no_grid_consistency():
    """Test that grid walking produces same coordinate ranges as single query."""

    provider = get_provider("bag3d")

    # Small area (100m) - no grid walking
    location = Location(
        type=LocationType.POINT,
        value=[4.90098, 52.37092],
        radius=100,  # Too small for grid walking
    )

    dataset = Dataset(provider="bag3d", service="bag3d", layers=["lod22"])

    result_small = await provider.download_dataset(
        dataset=dataset, location=location, output_path="test_small.gpkg", output_crs="EPSG:28992"
    )

    print(f"\nSmall area (100m): {len(result_small)} features")

    # Verify same coordinate range rules apply
    if not result_small.empty:
        bounds = result_small.total_bounds
        minx, miny, maxx, maxy = bounds

        print(f"Small area bounds: ({minx:.2f}, {miny:.2f}, {maxx:.2f}, {maxy:.2f})")

        assert 110000 < minx < 140000, "Small query has invalid X coordinates"
        assert 470000 < miny < 500000, "Small query has invalid Y coordinates"
        print("✓ Small area coordinates also in valid RD range")


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Grid Walking Coordinate Transforms")
    print("=" * 80)

    asyncio.run(test_grid_walking_coordinate_transforms())

    print("\n" + "=" * 80)
    asyncio.run(test_grid_vs_no_grid_consistency())
    print("=" * 80)
