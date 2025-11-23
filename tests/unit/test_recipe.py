"""Unit tests for Recipe models."""

from pathlib import Path

import pytest

from giskit.core.recipe import (
    Dataset,
    Location,
    LocationType,
    Output,
    OutputFormat,
    Recipe,
)


class TestLocation:
    """Tests for Location model."""

    def test_address_location_valid(self):
        """Test valid address location."""
        loc = Location(
            type=LocationType.ADDRESS,
            value="Dam 1, Amsterdam",
            radius=500,
        )
        assert loc.type == LocationType.ADDRESS
        assert loc.value == "Dam 1, Amsterdam"
        assert loc.radius == 500
        assert loc.crs == "EPSG:4326"

    def test_address_location_missing_radius(self):
        """Test address location requires radius."""
        with pytest.raises(ValueError, match="Radius required"):
            Location(
                type=LocationType.ADDRESS,
                value="Dam 1, Amsterdam",
            )

    def test_address_location_empty_string(self):
        """Test address cannot be empty."""
        with pytest.raises(ValueError, match="non-empty string"):
            Location(
                type=LocationType.ADDRESS,
                value="",
                radius=500,
            )

    def test_point_location_valid(self):
        """Test valid point location."""
        loc = Location(
            type=LocationType.POINT,
            value=[4.9041, 52.3676],
            radius=1000,
        )
        assert loc.type == LocationType.POINT
        assert loc.value == [4.9041, 52.3676]
        assert loc.radius == 1000

    def test_point_location_invalid_coords(self):
        """Test point must be [lon, lat]."""
        with pytest.raises(ValueError, match="Point must be"):
            Location(
                type=LocationType.POINT,
                value=[4.9041],  # Only one coordinate
                radius=1000,
            )

    def test_bbox_location_valid(self):
        """Test valid bbox location."""
        loc = Location(
            type=LocationType.BBOX,
            value=[4.88, 52.36, 4.92, 52.38],
        )
        assert loc.type == LocationType.BBOX
        assert loc.value == [4.88, 52.36, 4.92, 52.38]
        assert loc.radius is None

    def test_bbox_location_invalid_bounds(self):
        """Test bbox min must be < max."""
        with pytest.raises(ValueError, match="min must be < max"):
            Location(
                type=LocationType.BBOX,
                value=[4.92, 52.36, 4.88, 52.38],  # minx > maxx
            )

    def test_bbox_location_with_radius_fails(self):
        """Test bbox cannot have radius."""
        with pytest.raises(ValueError, match="not applicable"):
            Location(
                type=LocationType.BBOX,
                value=[4.88, 52.36, 4.92, 52.38],
                radius=500,
            )

    def test_polygon_location_valid(self):
        """Test valid polygon location."""
        loc = Location(
            type=LocationType.POLYGON,
            value=[
                [4.88, 52.36],
                [4.92, 52.36],
                [4.90, 52.38],
                [4.88, 52.36],
            ],
        )
        assert loc.type == LocationType.POLYGON
        assert len(loc.value) == 4

    def test_polygon_location_too_few_points(self):
        """Test polygon must have at least 3 points."""
        with pytest.raises(ValueError, match="at least 3 points"):
            Location(
                type=LocationType.POLYGON,
                value=[[4.88, 52.36], [4.92, 52.36]],
            )

    def test_radius_bounds(self):
        """Test radius must be within bounds."""
        with pytest.raises(ValueError):
            Location(
                type=LocationType.ADDRESS,
                value="Dam 1, Amsterdam",
                radius=-100,  # Negative
            )

        with pytest.raises(ValueError):
            Location(
                type=LocationType.ADDRESS,
                value="Dam 1, Amsterdam",
                radius=100000,  # > 50km
            )


class TestDataset:
    """Tests for Dataset model."""

    def test_pdok_dataset_valid(self):
        """Test valid PDOK dataset."""
        ds = Dataset(
            provider="pdok",
            service="bgt",
            layers=["pand", "wegdeel"],
        )
        assert ds.provider == "pdok"
        assert ds.service == "bgt"
        assert ds.layers == ["pand", "wegdeel"]

    def test_osm_dataset_valid(self):
        """Test valid OSM dataset."""
        ds = Dataset(
            provider="osm",
            query="amenity=restaurant",
        )
        assert ds.provider == "osm"
        assert ds.query == "amenity=restaurant"

    def test_dataset_requires_specification(self):
        """Test dataset must have service/query/product."""
        with pytest.raises(ValueError, match="Must specify"):
            Dataset(provider="pdok")

    def test_dataset_extra_params(self):
        """Test dataset can have extra parameters."""
        ds = Dataset(
            provider="copernicus",
            product="dem",
            resolution=30,
            extra={"version": "v2", "format": "geotiff"},
        )
        assert ds.extra["version"] == "v2"
        assert ds.extra["format"] == "geotiff"


class TestOutput:
    """Tests for Output model."""

    def test_output_gpkg_default(self):
        """Test default GPKG output."""
        out = Output(path=Path("data.gpkg"))
        assert out.path == Path("data.gpkg")
        assert out.format == OutputFormat.GPKG
        assert out.crs == "EPSG:4326"
        assert out.overwrite is False

    def test_output_auto_extension(self):
        """Test output auto-fixes extension."""
        out = Output(
            path=Path("data.txt"),
            format=OutputFormat.GPKG,
        )
        assert out.path == Path("data.gpkg")

    def test_output_with_options(self):
        """Test output with custom options."""
        out = Output(
            path=Path("output.gpkg"),
            format=OutputFormat.GPKG,
            crs="EPSG:28992",
            overwrite=True,
            layer_prefix="amsterdam_",
        )
        assert out.crs == "EPSG:28992"
        assert out.overwrite is True
        assert out.layer_prefix == "amsterdam_"


class TestRecipe:
    """Tests for Recipe model."""

    def test_recipe_valid(self):
        """Test valid complete recipe."""
        recipe = Recipe(
            name="Test recipe",
            description="Test description",
            location=Location(
                type=LocationType.ADDRESS,
                value="Dam 1, Amsterdam",
                radius=500,
            ),
            datasets=[
                Dataset(provider="pdok", service="bgt", layers=["pand"]),
                Dataset(provider="osm", query="amenity=restaurant"),
            ],
            output=Output(path=Path("output.gpkg")),
        )
        assert recipe.name == "Test recipe"
        assert len(recipe.datasets) == 2
        assert recipe.output.path == Path("output.gpkg")

    def test_recipe_minimal(self):
        """Test minimal recipe (no name/description)."""
        recipe = Recipe(
            location=Location(
                type=LocationType.BBOX,
                value=[4.88, 52.36, 4.92, 52.38],
            ),
            datasets=[
                Dataset(provider="pdok", service="bgt", layers=["pand"]),
            ],
            output=Output(path=Path("output.gpkg")),
        )
        assert recipe.name is None
        assert recipe.description is None
        assert len(recipe.datasets) == 1

    def test_recipe_requires_datasets(self):
        """Test recipe must have at least one dataset."""
        with pytest.raises(ValueError):
            Recipe(
                location=Location(
                    type=LocationType.BBOX,
                    value=[4.88, 52.36, 4.92, 52.38],
                ),
                datasets=[],
                output=Output(path=Path("output.gpkg")),
            )

    async def test_recipe_get_bbox_wgs84_direct(self):
        """Test get_bbox_wgs84 with direct bbox location."""
        recipe = Recipe(
            location=Location(
                type=LocationType.BBOX,
                value=[4.88, 52.36, 4.92, 52.38],
            ),
            datasets=[
                Dataset(provider="pdok", service="bgt", layers=["pand"]),
            ],
            output=Output(path=Path("output.gpkg")),
        )
        bbox = await recipe.get_bbox_wgs84()
        assert bbox == (4.88, 52.36, 4.92, 52.38)

    async def test_recipe_get_bbox_wgs84_address(self):
        """Test get_bbox_wgs84 with address location (geocoding)."""
        recipe = Recipe(
            location=Location(
                type=LocationType.ADDRESS,
                value="Dam 1, Amsterdam",
                radius=500,
            ),
            datasets=[
                Dataset(provider="pdok", service="bgt", layers=["pand"]),
            ],
            output=Output(path=Path("output.gpkg")),
        )
        # This should geocode the address and create a bbox
        bbox = await recipe.get_bbox_wgs84()
        # Verify it returns a valid bbox (4 floats)
        assert len(bbox) == 4
        assert all(isinstance(x, float) for x in bbox)
        # Amsterdam roughly 4.8-5.0 lon, 52.3-52.4 lat
        assert 4.5 < bbox[0] < 5.5 and 4.5 < bbox[2] < 5.5
        assert 52.0 < bbox[1] < 53.0 and 52.0 < bbox[3] < 53.0

    def test_recipe_to_dict(self):
        """Test recipe serialization to dict."""
        recipe = Recipe(
            name="Test",
            location=Location(
                type=LocationType.BBOX,
                value=[4.88, 52.36, 4.92, 52.38],
            ),
            datasets=[
                Dataset(provider="pdok", service="bgt", layers=["pand"]),
            ],
            output=Output(path=Path("output.gpkg")),
        )
        data = recipe.model_dump(mode="json")
        assert data["name"] == "Test"
        assert data["location"]["type"] == "bbox"
        assert len(data["datasets"]) == 1
