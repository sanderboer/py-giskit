# CRS (Coordinate Reference System) Handling in GISKit

## Overview

GISKit handles coordinate transformations automatically across different protocols and providers. This document explains how CRS handling works for each protocol.

## Default CRS

- **Default Input CRS**: `EPSG:4326` (WGS84 - lat/lon)
- **Default Output CRS**: `EPSG:4326` (WGS84)
- **Netherlands CRS**: `EPSG:28992` (RD New / Rijksdriehoekscoördinaten)

---

## Protocol-Specific CRS Behavior

### OGC API Features

**Input CRS**: `EPSG:4326` (required by OGC Features spec)
**Output CRS**: Configurable (auto-transforms)

```python
# OGC Features always accepts WGS84 bbox
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)  # minx, miny, maxx, maxy

# Downloads in WGS84, then transforms to target CRS
gdf = await protocol.get_features(
    bbox=bbox_wgs84,           # Must be WGS84
    crs="EPSG:28992"           # Output will be transformed to RD New
)

assert gdf.crs == "EPSG:28992"
```

**Behavior**:
1. Accepts bbox in `EPSG:4326` only
2. Downloads data from service (always in `EPSG:4326`)
3. Auto-transforms to target CRS if `crs != "EPSG:4326"`

---

### WMTS (Web Map Tile Service)

**Input CRS**: Must match `TileMatrixSet` (usually `EPSG:28992`)
**Output CRS**: Same as input (no transformation)

```python
# WMTS requires bbox in TileMatrixSet CRS
protocol = WMTSProtocol(
    base_url="https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0",
    layer="Actueel_ortho25",
    tile_matrix_set="EPSG:28992"
)

# Bbox MUST be in EPSG:28992 (RD New)
bbox_rd = (121000, 487000, 122000, 488000)  # RD coordinates

image = await protocol.get_coverage(
    bbox=bbox_rd,              # MUST match TileMatrixSet CRS
    crs="EPSG:28992"           # Must match TileMatrixSet
)
```

**Behavior**:
1. Validates that input CRS matches `TileMatrixSet`
2. Raises `ValueError` if CRS mismatch
3. No automatic transformation (tiles are pre-rendered)

**Important**: If you have WGS84 coordinates, transform before calling WMTS:

```python
from giskit.core.spatial import transform_bbox

# Convert WGS84 to RD New
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)
bbox_rd = transform_bbox(bbox_wgs84, "EPSG:4326", "EPSG:28992")

# Now use with WMTS
image = await protocol.get_coverage(bbox=bbox_rd, crs="EPSG:28992")
```

---

### WCS (Web Coverage Service)

**Input CRS**: Flexible (auto-transforms internally)
**Output CRS**: Configurable

```python
# WCS handles transformation automatically
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)

data = await protocol.get_coverage(
    bbox=bbox_wgs84,           # Can be any CRS
    crs="EPSG:4326",           # Input bbox CRS
    product="dtm_05m",
    resolution=0.5
)

# Or with RD coordinates
bbox_rd = (121000, 487000, 122000, 488000)
data = await protocol.get_coverage(
    bbox=bbox_rd,
    crs="EPSG:28992",
    product="dtm_05m",
    resolution=0.5
)
```

**Behavior**:
1. Accepts bbox in any CRS (specified by `crs` parameter)
2. Transforms bbox to service's native CRS if needed
3. Downloads coverage data
4. Returns data with proper CRS metadata

---

## Location to BBox Conversion

Use `location_to_bbox()` helper for unified conversion:

```python
from giskit.core.spatial import location_to_bbox
from giskit.core.recipe import Location, LocationType

# Address → bbox in RD New
loc = Location(
    type=LocationType.ADDRESS,
    value="Dam 1, Amsterdam",
    radius=500
)
bbox_rd = await location_to_bbox(loc, target_crs="EPSG:28992")

# Point → bbox in WGS84
loc = Location(
    type=LocationType.POINT,
    value=[52.3676, 4.9041],
    radius=1000,
    crs="EPSG:4326"
)
bbox_wgs84 = await location_to_bbox(loc, target_crs="EPSG:4326")

# Bbox → transform if needed
loc = Location(
    type=LocationType.BBOX,
    value=[4.88, 52.36, 4.92, 52.38],
    crs="EPSG:4326"
)
bbox_rd = await location_to_bbox(loc, target_crs="EPSG:28992")
```

---

## CRS Transformation Utilities

### Transform Bbox

```python
from giskit.core.spatial import transform_bbox

# WGS84 → RD New
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)
bbox_rd = transform_bbox(bbox_wgs84, "EPSG:4326", "EPSG:28992")
# → (120000, 486000, 124000, 490000)  # approximate

# RD New → WGS84
bbox_wgs84 = transform_bbox(bbox_rd, "EPSG:28992", "EPSG:4326")
```

### Transform Point

```python
from giskit.core.spatial import transform_point

# WGS84 → RD New
lon, lat = 4.9041, 52.3676  # Amsterdam Dam Square
x, y = transform_point(lon, lat, "EPSG:4326", "EPSG:28992")
# → (121600, 487300)  # approximate RD coordinates

# RD New → WGS84
lon, lat = transform_point(x, y, "EPSG:28992", "EPSG:4326")
```

### Buffer Point to Bbox

```python
from giskit.core.spatial import buffer_point_to_bbox

# Create 500m bbox around point (in WGS84)
lon, lat = 4.9041, 52.3676
radius_m = 500
bbox = buffer_point_to_bbox(lon, lat, radius_m, crs="EPSG:4326")
# → (4.897, 52.363, 4.911, 52.372)  # approximate
```

---

## Common CRS Codes

| Code | Name | Region | Units |
|------|------|--------|-------|
| `EPSG:4326` | WGS84 | Global | Degrees |
| `EPSG:28992` | RD New | Netherlands | Meters |
| `EPSG:3857` | Web Mercator | Global (web maps) | Meters |
| `EPSG:4258` | ETRS89 | Europe | Degrees |
| `EPSG:25831` | ETRS89 UTM 31N | Belgium/Netherlands | Meters |
| `EPSG:31370` | Belgian Lambert 72 | Belgium | Meters |

---

## Best Practices

### 1. Use WGS84 for Recipes

Always use `EPSG:4326` (WGS84) in recipe files for portability:

```json
{
  "location": {
    "type": "address",
    "value": "Dam 1, Amsterdam",
    "radius": 500,
    "crs": "EPSG:4326"
  },
  "output": {
    "path": "./data.gpkg",
    "crs": "EPSG:28992"
  }
}
```

### 2. Transform Before WMTS

WMTS requires exact CRS match - always transform first:

```python
# BAD - will raise ValueError
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)
image = await wmts_protocol.get_coverage(bbox=bbox_wgs84, crs="EPSG:4326")
# ❌ ValueError: CRS EPSG:4326 does not match TileMatrixSet EPSG:28992

# GOOD - transform first
bbox_rd = transform_bbox(bbox_wgs84, "EPSG:4326", "EPSG:28992")
image = await wmts_protocol.get_coverage(bbox=bbox_rd, crs="EPSG:28992")
# ✅ Works!
```

### 3. Use `location_to_bbox()` Helper

Don't reimplement bbox conversion - use the helper:

```python
# BAD - manual conversion
if location.type == "address":
    lon, lat = await geocode(location.value)
    bbox = buffer_point_to_bbox(lon, lat, location.radius)
    if target_crs != "EPSG:4326":
        bbox = transform_bbox(bbox, "EPSG:4326", target_crs)
# ... repeat for point, bbox, polygon

# GOOD - use helper
bbox = await location_to_bbox(location, target_crs="EPSG:28992")
```

### 4. Validate CRS

Check CRS validity before using:

```python
from giskit.core.spatial import validate_crs, get_crs_info

# Validate
if not validate_crs("EPSG:28992"):
    raise ValueError("Invalid CRS")

# Get info
info = get_crs_info("EPSG:28992")
print(info)
# {
#   "name": "Amersfoort / RD New",
#   "type": "Projected CRS",
#   "area": "Netherlands - onshore",
#   "unit": "metre"
# }
```

---

## Protocol Comparison Table

| Protocol | Input CRS | Auto-Transform | Notes |
|----------|-----------|----------------|-------|
| **OGC Features** | `EPSG:4326` only | ✅ Yes | Spec requires WGS84 |
| **WMTS** | Must match TileMatrixSet | ❌ No | Pre-rendered tiles |
| **WCS** | Any (specify with `crs`) | ✅ Yes | Service transforms |

---

## Migration Guide

### From Old Code

If you're updating code that doesn't handle CRS properly:

**Before**:
```python
# Assumed everything was in same CRS
bbox = (121000, 487000, 122000, 488000)
gdf = await protocol.get_features(bbox=bbox)
# ❌ Might fail if protocol expects WGS84
```

**After**:
```python
# Explicit CRS handling
bbox_rd = (121000, 487000, 122000, 488000)
bbox_wgs84 = transform_bbox(bbox_rd, "EPSG:28992", "EPSG:4326")
gdf = await protocol.get_features(bbox=bbox_wgs84, crs="EPSG:28992")
# ✅ Explicit transformation
```

Or use the helper:

```python
from giskit.core.spatial import location_to_bbox

loc = Location(type=LocationType.BBOX, value=bbox_rd, crs="EPSG:28992")
bbox_wgs84 = await location_to_bbox(loc, target_crs="EPSG:4326")
gdf = await protocol.get_features(bbox=bbox_wgs84, crs="EPSG:28992")
```

---

## Troubleshooting

### Error: "CRS does not match TileMatrixSet"

**Problem**: WMTS requires exact CRS match

**Solution**: Transform bbox before calling WMTS
```python
bbox_wgs84 = (4.88, 52.36, 4.92, 52.38)
bbox_rd = transform_bbox(bbox_wgs84, "EPSG:4326", "EPSG:28992")
```

### Error: "Invalid bbox: minx >= maxx"

**Problem**: Bbox coordinates swapped or in wrong order

**Solution**: Check bbox format is (minx, miny, maxx, maxy)
```python
# WRONG
bbox = (52.36, 4.88, 52.38, 4.92)  # lat/lon order

# CORRECT
bbox = (4.88, 52.36, 4.92, 52.38)  # lon/lat order
```

### Error: "Failed to transform bbox"

**Problem**: Invalid CRS code

**Solution**: Validate CRS first
```python
from giskit.core.spatial import validate_crs

if not validate_crs("EPSG:99999"):
    print("Invalid CRS!")
```

---

## Future Improvements

Planned enhancements for CRS handling:

1. **Auto-detect TileMatrixSet** - WMTS could detect and transform automatically
2. **CRS aliases** - Support "WGS84", "RD", etc. as aliases
3. **Unit detection** - Auto-detect if CRS uses degrees vs meters
4. **More TileMatrixSets** - Support EPSG:3857, EPSG:4258, etc.
5. **Vertical CRS** - Support for elevation datums (NAP, etc.)

---

## References

- [EPSG.io](https://epsg.io/) - CRS lookup and conversion
- [Proj](https://proj.org/) - Coordinate transformation library
- [OGC API Features CRS](https://docs.ogc.org/is/17-069r4/17-069r4.html#_coordinate_reference_systems)
- [WMTS Specification](https://www.ogc.org/standards/wmts)
- [Rijksdriehoekscoördinaten](https://nl.wikipedia.org/wiki/Rijksdriehoeksco%C3%B6rdinaten)
