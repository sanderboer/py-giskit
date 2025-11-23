"""CityJSON format parser for 3D BAG data.

CityJSON is a JSON-based encoding for storing 3D city models.
This parser is specifically designed for the 3DBAG API (api.3dbag.nl).

The 3DBAG API returns CityJSON features in an OGC API Features-like format:
- Features have a "CityObjects" property instead of standard GeoJSON geometry
- Each feature has a shared "vertices" array
- Geometry is defined by indices into the vertices array
- Multiple LODs (Level of Detail) are available per building:
  - LOD 0: 2D footprint (from Building object)
  - LOD 1.2, 1.3, 2.2: 3D models (from BuildingPart objects)

CRITICAL CityJSON 2.0 Quirk:
- Vertices are INTEGERS that require transformation
- Each pagination page has its own transform (scale/translate) in metadata
- Real coordinates = vertex * scale + translate
- Applying wrong transform causes coordinate errors!

Example feature structure:
{
  "metadata": {
    "transform": {
      "scale": [0.001, 0.001, 0.001],
      "translate": [80000.0, 429000.0, 0.0]
    }
  },
  "features": [{
    "vertices": [[123, 456, 789], ...],  # INTEGER indices!
    "CityObjects": {
      "NL.IMBAG.Pand.XXX": {
        "type": "Building",
        "geometry": [{"lod": "0", "type": "MultiSurface", "boundaries": [...]}],
        "attributes": {...}
      },
      "NL.IMBAG.Pand.XXX-0": {
        "type": "BuildingPart",
        "geometry": [
          {"lod": "1.2", "type": "Solid", "boundaries": [...]},
          {"lod": "2.2", "type": "Solid", "boundaries": [...]}
        ]
      }
    }
  }]
}
"""

from typing import Optional

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon


def cityjson_to_geodataframe(cityjson_data: dict, lod: str = "0") -> gpd.GeoDataFrame:
    """Convert CityJSON features from 3DBAG API to GeoDataFrame.

    CRITICAL: CityJSON 2.0 uses per-page transforms for vertex compression.
    Each pagination page has its own transform (scale/translate) in metadata.
    Vertices are integers that MUST be scaled: real_coord = vertex * scale + translate.

    Args:
        cityjson_data: CityJSON data (GeoJSON-like with CityObjects and metadata.transform)
        lod: Level of Detail to extract (0 = footprint, 2.2 = 3D model)

    Returns:
        GeoDataFrame with building footprints or 3D models
    """
    features = cityjson_data.get("features", [])
    if not features:
        return gpd.GeoDataFrame()

    # Extract transform from metadata (CityJSON 2.0 per-page transform)
    # This is CRITICAL - without this, coordinates will be completely wrong!
    page_transform = None
    if "metadata" in cityjson_data and isinstance(cityjson_data["metadata"], dict):
        page_transform = cityjson_data["metadata"].get("transform")

    rows = []

    for feature in features:
        # Get shared vertices array for this feature
        vertices = feature.get("vertices", [])

        # Extract CityObjects (buildings)
        city_objects = feature.get("CityObjects", {})

        # Find the main Building object to get attributes
        main_building = None
        main_building_id = None
        for obj_id, obj in city_objects.items():
            if obj.get("type") == "Building":
                main_building = obj
                main_building_id = obj_id
                break

        if not main_building:
            continue

        # Get attributes from main building
        attrs = main_building.get("attributes", {})

        # Extract geometry based on LOD
        geometry = None

        if lod == "0":
            # LOD 0: 2D footprint from Building object
            geometry = _extract_lod0_geometry(main_building, vertices, page_transform)
        else:
            # LOD 1.2/1.3/2.2: 3D model from BuildingPart children
            # Find BuildingPart with requested LOD
            for _obj_id, obj in city_objects.items():
                if obj.get("type") == "BuildingPart":
                    geometry = _extract_lod_geometry(obj, vertices, lod, page_transform)
                    if geometry:
                        break  # Found requested LOD

        # Skip if no geometry found
        if geometry is None:
            continue

        # Extract key attributes
        row = {
            "geometry": geometry,
            "identificatie": attrs.get("identificatie", main_building_id or "unknown"),
            "bouwjaar": attrs.get("oorspronkelijkbouwjaar"),
            "status": attrs.get("status"),
            "h_dak_max": attrs.get("b3_h_dak_max"),
            "h_dak_min": attrs.get("b3_h_dak_min"),
            "h_dak_50p": attrs.get("b3_h_dak_50p"),
            "h_maaiveld": attrs.get("b3_h_maaiveld"),
            "opp_grond": attrs.get("b3_opp_grond"),
            "opp_dak_plat": attrs.get("b3_opp_dak_plat"),
            "opp_dak_schuin": attrs.get("b3_opp_dak_schuin"),
            "dak_type": attrs.get("b3_dak_type"),
        }

        # Add LOD-specific attributes
        if lod != "0":
            lod_key = lod.replace(".", "")
            row[f"volume_lod{lod_key}"] = attrs.get(f"b3_volume_lod{lod_key}")

        rows.append(row)

    if not rows:
        return gpd.GeoDataFrame()

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:28992")
    return gdf


def _extract_lod0_geometry(
    city_object: dict, vertices: list, transform: Optional[dict] = None
) -> Optional[Polygon]:
    """Extract LOD 0 (2D footprint) geometry from CityObject.

    Args:
        city_object: CityJSON building object
        vertices: Shared vertices array (integer indices if transform provided)
        transform: CityJSON transform (scale/translate) for vertices

    Returns:
        Shapely Polygon or None
    """
    geom_list = city_object.get("geometry", [])

    for geom in geom_list:
        lod = geom.get("lod")
        if str(lod) == "0":
            boundaries = geom.get("boundaries", [])
            geom_type = geom.get("type", "")

            if geom_type == "MultiSurface" and boundaries and vertices:
                # Extract first surface as footprint
                coords = []
                for surface in boundaries:
                    if surface:
                        outer_ring = surface[0]
                        ring_coords = []
                        for vertex_idx in outer_ring:
                            if vertex_idx < len(vertices):
                                v = vertices[vertex_idx]
                                # Apply transform if available (CityJSON 2.0)
                                if transform and "scale" in transform and "translate" in transform:
                                    scale = transform["scale"]
                                    translate = transform["translate"]
                                    x = v[0] * scale[0] + translate[0]
                                    y = v[1] * scale[1] + translate[1]
                                    ring_coords.append((x, y))
                                else:
                                    # No transform, use raw vertices
                                    ring_coords.append((v[0], v[1]))
                        if ring_coords:
                            coords.append(ring_coords)

                if coords:
                    return Polygon(coords[0])

    return None


def _extract_lod_geometry(
    city_object: dict, vertices: list, lod: str, transform: Optional[dict] = None
) -> Optional[MultiPolygon]:
    """Extract 3D geometry for a specific LOD from BuildingPart.

    Args:
        city_object: CityJSON BuildingPart object
        vertices: Shared vertices array (integer indices if transform provided)
        lod: Level of Detail (e.g. "2.2")
        transform: CityJSON transform (scale/translate) for vertices

    Returns:
        Shapely MultiPolygon with Z coordinates (3D surfaces) or None
    """
    geom_list = city_object.get("geometry", [])

    for geom in geom_list:
        geom_lod = str(geom.get("lod", ""))
        if geom_lod == lod:
            boundaries = geom.get("boundaries", [])
            geom_type = geom.get("type", "")

            if geom_type == "Solid" and boundaries and vertices:
                # Solid has shells -> surfaces -> rings
                # Extract all surfaces as 3D polygons
                surfaces = []
                for shell in boundaries:
                    for surface in shell:
                        if surface:
                            outer_ring = surface[0]
                            ring_coords = []
                            for vertex_idx in outer_ring:
                                if vertex_idx < len(vertices):
                                    v = vertices[vertex_idx]
                                    # Apply transform if available (CityJSON 2.0)
                                    if (
                                        transform
                                        and "scale" in transform
                                        and "translate" in transform
                                    ):
                                        scale = transform["scale"]
                                        translate = transform["translate"]
                                        x = v[0] * scale[0] + translate[0]
                                        y = v[1] * scale[1] + translate[1]
                                        z = (v[2] * scale[2] + translate[2]) if len(v) > 2 else 0
                                        ring_coords.append((x, y, z))
                                    else:
                                        # No transform, use raw vertices
                                        ring_coords.append((v[0], v[1], v[2] if len(v) > 2 else 0))
                            if ring_coords:
                                try:
                                    surfaces.append(Polygon(ring_coords))
                                except Exception:
                                    pass  # Skip invalid polygons

                if surfaces:
                    return MultiPolygon(surfaces)

    return None
