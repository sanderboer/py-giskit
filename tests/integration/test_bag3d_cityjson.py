"""Integration tests for BAG3D API and CityJSON format quirks.

These tests validate that the BAG3D API returns CityJSON format with
per-page transforms, as documented in the quirks system.

CRITICAL: These tests verify the transform quirks that caused production
issues in Sitedb (see bag3d_downloader.py:87-100).
"""

import pytest
import requests

from giskit.protocols.quirks import get_format_quirks, get_quirks


class TestBAG3DAPICityJSON:
    """Test BAG3D API returns CityJSON format with expected quirks."""

    def test_bag3d_api_available(self):
        """Test BAG3D API is accessible."""
        response = requests.get("https://api.3dbag.nl/api.html", timeout=10)
        assert response.status_code == 200, "BAG3D API documentation not accessible"

    def test_bag3d_returns_cityjson_format(self):
        """Test BAG3D API returns CityJSON format (not GeoJSON)."""
        # Query a small area in Amsterdam (Dam Square)
        url = "https://api.3dbag.nl/collections/pand/items"
        params = {
            "limit": 1,  # Just get 1 feature to test format
            "bbox": "4.89,52.37,4.90,52.38",  # Small bbox around Dam Square
        }

        response = requests.get(url, params=params, timeout=30)
        assert response.status_code == 200, f"BAG3D API failed: {response.status_code}"

        data = response.json()

        # CityJSON should have these top-level keys
        assert "type" in data
        assert data["type"] == "FeatureCollection" or "CityJSON" in str(data.get("type", ""))

        # Check for CityJSON-specific structure
        # CityJSON has either 'vertices' or features have CityJSON geometry
        has_cityjson_structure = (
            "vertices" in data  # CityJSON 1.x/2.0 format
            or (
                "metadata" in data and "transform" in data.get("metadata", {})
            )  # Transform metadata
            or any(
                "CityObjects" in str(f) for f in data.get("features", [])[:1]
            )  # CityObjects in features
        )

        assert has_cityjson_structure, f"Expected CityJSON format but got: {list(data.keys())}"

    def test_bag3d_has_transform_metadata(self):
        """Test BAG3D returns transform metadata (CRITICAL for coordinate scaling)."""
        url = "https://api.3dbag.nl/collections/pand/items"
        params = {
            "limit": 1,
            "bbox": "4.89,52.37,4.90,52.38",
        }

        response = requests.get(url, params=params, timeout=30)
        assert response.status_code == 200

        data = response.json()

        # CityJSON format should have transform in metadata
        has_transform = (
            ("metadata" in data and "transform" in data["metadata"])
            or ("transform" in data)  # Some versions put it at top level
        )

        if has_transform:
            # Extract transform
            transform = data.get("transform") or data.get("metadata", {}).get("transform")

            # Verify transform has scale and translate
            assert "scale" in transform, "Transform missing 'scale' array"
            assert "translate" in transform, "Transform missing 'translate' array"

            # Scale and translate should be 3D arrays (x, y, z)
            assert (
                len(transform["scale"]) == 3
            ), f"Scale should be [x,y,z] but got: {transform['scale']}"
            assert (
                len(transform["translate"]) == 3
            ), f"Translate should be [x,y,z] but got: {transform['translate']}"

            print(
                f"✓ Transform found: scale={transform['scale']}, translate={transform['translate']}"
            )
        else:
            # If no transform, vertices should be regular floats (not integers)
            pytest.skip("BAG3D API format may have changed - no transform found")

    def test_bag3d_vertices_are_integers_when_transform_present(self):
        """Test that vertices are integers when transform is present (CityJSON compression)."""
        url = "https://api.3dbag.nl/collections/pand/items"
        params = {
            "limit": 1,
            "bbox": "4.89,52.37,4.90,52.38",
        }

        response = requests.get(url, params=params, timeout=30)
        assert response.status_code == 200

        data = response.json()

        # Check if vertices array exists
        if "vertices" in data and data["vertices"]:
            vertices = data["vertices"]

            # CityJSON compression: vertices should be integers
            first_vertex = vertices[0]
            assert len(first_vertex) == 3, "Vertices should be 3D (x, y, z)"

            # Check if vertices are integers (CityJSON compression)
            are_integers = all(isinstance(coord, int) for coord in first_vertex)

            if are_integers:
                print(
                    f"✓ Vertices are integers: {first_vertex} (requires transform to get real coords)"
                )

                # If vertices are integers, transform MUST be present
                has_transform = ("metadata" in data and "transform" in data["metadata"]) or (
                    "transform" in data
                )
                assert has_transform, (
                    "CRITICAL: Vertices are integers but no transform found! "
                    "Cannot compute real coordinates without scale/translate."
                )
            else:
                print(f"ℹ Vertices are floats: {first_vertex} (no transform needed)")
        else:
            pytest.skip("No vertices array found in response")

    @pytest.mark.parametrize("page_num", [0, 1])
    def test_bag3d_transform_may_differ_per_page(self, page_num):
        """Test that different pagination pages may have different transforms.

        This is the CRITICAL quirk that caused production bugs in Sitedb!
        Each page can have its own scale/translate values.
        """
        url = "https://api.3dbag.nl/collections/pand/items"
        params = {
            "limit": 10,
            "bbox": "4.89,52.37,4.91,52.39",  # Larger area to get multiple pages
            "offset": page_num * 10,  # Pagination offset
        }

        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            pytest.skip(f"Page {page_num} not available")

        data = response.json()

        # Extract transform if present
        transform = data.get("transform") or data.get("metadata", {}).get("transform")

        if transform:
            print(
                f"Page {page_num} transform: scale={transform.get('scale')}, "
                f"translate={transform.get('translate')}"
            )

            # Save for comparison (in real implementation, you'd compare across pages)
            # This test just verifies transform exists per page
            assert "scale" in transform
            assert "translate" in transform
        else:
            pytest.skip("No transform in response")


class TestCityJSONQuirksValidation:
    """Validate that quirks system correctly identifies CityJSON format issues."""

    def test_cityjson_format_quirks_match_bag3d_reality(self):
        """Test that quirks system flags match actual BAG3D API behavior."""
        quirks = get_format_quirks("cityjson")

        # These should all be True based on actual BAG3D API behavior
        assert quirks.format_is_cityjson is True
        assert quirks.has_per_page_transform is True
        assert quirks.transform_applies_to_vertices is True
        assert quirks.vertices_are_integers is True
        assert quirks.geometry_in_city_objects is True
        assert quirks.has_lod_hierarchy is True

    def test_bag3d_quirks_warn_about_transform_bug(self):
        """Test that BAG3D quirks adequately warn about the per-page transform issue."""
        cityjson_quirks = get_format_quirks("cityjson")
        bag3d_quirks = get_quirks("bag3d", "ogc-features")

        # Both should warn about the transform issue
        for quirks in [cityjson_quirks, bag3d_quirks]:
            assert "transform" in quirks.description.lower()
            assert "page" in quirks.description.lower()

            # Should mention it's CRITICAL
            assert "CRITICAL" in quirks.description or "critical" in quirks.description.lower()
