# GISKit Architecture: BAG3D Integration

## Overview

GISKit integrates the **3DBAG API** (api.3dbag.nl) as an external service via the PDOK provider. Although BAG3D is not hosted by PDOK, it is included in the PDOK provider for user convenience.

## Data Sources Architecture

### 1. PDOK Services (api.pdok.nl)

**WFS Protocol:**
- **BAG** (Base Registry for Addresses and Buildings)
  - Protocol: WFS 2.0
  - Format: GeoJSON
  - Layers: `pand`, `verblijfsobject`

- **BRK** (Cadastre)
  - Protocol: WFS 2.0
  - Format: GeoJSON
  - Layers: `perceel`, `kadastrale_grens`, `bebouwing`, etc.

**OGC API Features:**
- **BGT** (Base Registry for Large-Scale Topography)
  - Protocol: OGC API Features
  - Format: GeoJSON
  - Layers: 46 topographic layers (pand, wegdeel, waterdeel, etc.)

### 2. External Services (NOT from PDOK)

**3DBAG API (api.3dbag.nl):**
- **BAG3D** (3D Building Models)
  - Protocol: OGC API Features-like interface
  - Format: **CityJSON** (not GeoJSON!)
  - Host: api.3dbag.nl (NOT api.pdok.nl)
  - Collection: `pand` (contains all LODs)
  - LODs: 0, 1.2, 1.3, 2.2

## CityJSON Format

### Structure

Normal GeoJSON:
```json
{
  "type": "Feature",
  "geometry": {"type": "Polygon", "coordinates": [...]},
  "properties": {...}
}
```

CityJSON (3DBAG):
```json
{
  "metadata": {
    "transform": {
      "scale": [0.001, 0.001, 0.001],
      "translate": [80000.0, 429000.0, 0.0]
    }
  },
  "vertices": [[123456, 789012, 3456], ...],  // INTEGER indices!
  "CityObjects": {
    "NL.IMBAG.Pand.XXX": {
      "type": "Building",
      "geometry": [
        {"lod": "0", "type": "MultiSurface", "boundaries": [[0,1,2,3]]}
      ],
      "attributes": {"bouwjaar": 1983, ...}
    },
    "NL.IMBAG.Pand.XXX-0": {
      "type": "BuildingPart",
      "geometry": [
        {"lod": "1.2", "type": "Solid", "boundaries": [...]},
        {"lod": "2.2", "type": "Solid", "boundaries": [...]}
      ]
    }
  }
}
```

### Key Differences

1. **No top-level geometry** - geometry is in CityObjects
2. **Vertices array** - coordinates are indices in shared array
3. **Multiple LODs** - multiple detail levels per building
4. **Type hierarchy** - Building (parent) and BuildingPart (children)

## ⚠️ CRITICAL: CityJSON 2.0 Transform (PER-PAGE!)

**WARNING**: This is the most critical aspect of BAG3D integration!

### The Problem

CityJSON 2.0 uses **per-page transforms** for vertex compression:

1. **Vertices are INTEGER arrays**, not float coordinates
2. **Each pagination page has ITS OWN transform** in `metadata.transform`
3. **Transform MUST be applied**: `real_coord = vertex * scale + translate`
4. **Wrong transform = wrong coordinates** (kilometers offset!)

### Transform Example

```json
{
  "metadata": {
    "transform": {
      "scale": [0.001, 0.001, 0.001],
      "translate": [80113.570, 429309.435, -1.302]
    }
  },
  "vertices": [
    [5455, 661895, 5567],  // INTEGER values
    [6157, 662045, 5567]
  ]
}
```

Correct transformation:
```python
# Vertex: [5455, 661895, 5567]
x = 5455 * 0.001 + 80113.570 = 80119.025 (RD coordinate)
y = 661895 * 0.001 + 429309.435 = 430971.330 (RD coordinate)
z = 5567 * 0.001 + (-1.302) = 4.265 (height in meters)
```

**WITHOUT transform**: you would use [5455, 661895] as coordinates → completely wrong location!

### Walking Grid & Multi-Page Downloads

When downloading large areas:
- API returns multiple pages (pagination)
- **Each page has a different transform**
- Features from different pages must be merged correctly
- **EACH feature must be transformed with ITS OWN page transform**

### Implementation in GISKit

**giskit/protocols/cityjson.py:**
```python
def cityjson_to_geodataframe(cityjson_data: dict, lod: str = "0"):
    # CRITICAL: Extract per-page transform from metadata
    page_transform = None
    if 'metadata' in cityjson_data and isinstance(cityjson_data['metadata'], dict):
        page_transform = cityjson_data['metadata'].get('transform')

    for feature in features:
        vertices = feature.get("vertices", [])

        # Apply transform to EACH vertex
        if transform and 'scale' in transform and 'translate' in transform:
            scale = transform['scale']
            translate = transform['translate']
            x = vertex[0] * scale[0] + translate[0]
            y = vertex[1] * scale[1] + translate[1]
            z = vertex[2] * scale[2] + translate[2]
```

**giskit/protocols/ogc_features.py:**
```python
# Process each page separately with its own transform
while True:
    response = await client.get(next_url)
    geojson = response.json()  # Contains metadata.transform for THIS page

    # Parse with THIS page's transform
    gdf = cityjson_to_geodataframe(geojson, lod=lod)
    all_gdfs.append(gdf)

    # Next page will have DIFFERENT transform!
    next_url = get_next_link(geojson)
```

### Comparison with Sitedb

Sitedb implementation (correct):
```python
# Download all pages first
for page in pages:
    page_transform = page['metadata']['transform']
    for feature in page['features']:
        feature['_page_transform'] = page_transform  # Tag each feature!
    all_features.extend(page['features'])

# Process later with correct transform per feature
for feature in all_features:
    transform = feature['_page_transform']  # Use feature's original page transform
    coords = apply_transform(vertices, transform)
```

GISKit implementation (also correct, but different):
```python
# Process each page immediately with its transform
for page in pages:
    page_transform = page['metadata']['transform']
    gdf = cityjson_to_geodataframe(page, transform=page_transform)
    all_gdfs.append(gdf)  # Already transformed to real coordinates

# Combine all GeoDataFrames (coordinates already correct)
combined = gpd.concat(all_gdfs)
```

### Verification

Test that transform works correctly:
```python
# Download BAG3D data
gdf = download_bag3d(bbox=(80062, 429311, 81062, 430311), lod="2.2")

# Check bounds - should be in RD range (80000-81000)
print(gdf.total_bounds)
# Expected: [80119.52, 429309.43, 80750.58, 430008.65]

# NOT: [5000, 600000, ...] (wrong - these are raw vertex indices!)
```

### Resources

- CityJSON 2.0 Transform Spec: https://www.cityjson.org/specs/2.0.0/#transform-object
- 3DBAG API: https://api.3dbag.nl/collections/pand
- GISKit Quirks: `giskit/config/quirks/formats.yml` (cityjson quirks)

## LOD (Level of Detail) Support

### LOD Levels in 3DBAG

- **LOD 0**: 2D footprint (polygon)
  - Source: `Building` object
  - Geometry: MultiSurface with XY coordinates

- **LOD 1.2**: Simple 3D block with flat roof
  - Source: `BuildingPart` object
  - Geometry: Solid with XYZ coordinates

- **LOD 1.3**: 3D block with roof geometry
  - Source: `BuildingPart` object
  - Geometry: Solid with XYZ coordinates

- **LOD 2.2**: Detailed 3D model (roof details)
  - Source: `BuildingPart` object
  - Geometry: Solid with XYZ coordinates
  - Attributes: volume_lod22, daktype, etc.

### Layer Mapping

Recipe request:
```json
{
  "service": "bag3d",
  "layers": ["pand", "lod22"]
}
```

How it works:
1. `pand` → downloads "pand" collection, parsed as LOD 0 (2D)
2. `lod22` → downloads "pand" collection, parsed as LOD 2.2 (3D)

API call for both:
```
GET https://api.3dbag.nl/collections/pand/items?bbox=...
```

Parser detection (in `ogc_features.py`):
```python
if collection_id.startswith("lod"):
    lod_num = collection_id[3:]  # "lod22" → "22"
    lod = f"{lod_num[0]}.{lod_num[1]}"  # "22" → "2.2"
else:
    lod = "0"  # Default: footprint

# All LODs come from the same API response!
gdf = cityjson_to_geodataframe(geojson, lod=lod)
```

## Implementation Details

### Files Modified

1. **giskit/protocols/cityjson.py** (NEW)
   - CityJSON parser for 3DBAG API
   - Extracts LOD 0 from Building objects
   - Extracts LOD 1.2/1.3/2.2 from BuildingPart objects
   - Converts vertices + boundaries to Shapely geometry

2. **giskit/protocols/ogc_features.py**
   - Detects CityJSON format (looks for "CityObjects")
   - Recognizes LOD layers (lod22, lod12, etc.)
   - Maps lod* layers to "pand" collection
   - Passes LOD parameter to CityJSON parser

3. **giskit/providers/pdok.py**
   - Registers bag3d as external service
   - URL: https://api.3dbag.nl (not api.pdok.nl!)
   - Format: cityjson (not geojson!)
   - Special handling for LOD layers

4. **giskit/cli/main.py**
   - Adds _metadata layer to GeoPackage output
   - Contains: address, center point, bbox, date, CRS

## Usage Example

```python
from giskit.core.recipe import Recipe

recipe = Recipe.from_file("site_underlegger.json")

# Recipe includes:
{
  "provider": "pdok",
  "service": "bag3d",
  "layers": ["pand", "lod22"]  # 2D + 3D
}

# Results in 2 layers:
# - bag3d_pand: 2D footprints (LOD 0)
# - bag3d_lod22: 3D models (LOD 2.2) with Z-coordinates
```

## Output Structure

```
site_underlegger.gpkg
├── _metadata (1 feature)
│   └── address, x, y, radius, bbox, date, crs
│
├── bag_pand (23 features)
├── bag_verblijfsobject (38 features)
│
├── bag3d_pand (23 features)         ← LOD 0: 2D footprints
├── bag3d_lod22 (23 features)        ← LOD 2.2: 3D models with Z
│
├── brk_Perceel (52 features)
├── brk_KadastraleGrens (152 features)
└── bgt_* (26 layers, 1330 features)
```

## Key Insights

1. **BAG3D ≠ PDOK**: External service, different host, different format
2. **CityJSON ≠ GeoJSON**: Vertices array + boundaries instead of coordinates
3. **LOD = Virtual Layers**: All LODs in 1 API response, split in parser
4. **Building vs BuildingPart**: Parent has footprint, child has 3D
5. **Z-coordinates**: LOD 2.2 has true 3D geometry (MultiPolygon with Z)

## Performance Note

Because all LODs are in the same API response, downloading multiple LODs will
fetch the same features multiple times. For optimal performance, you could
download once and split locally, but the current implementation is simpler and
follows the layer-based design pattern.
