# GISKit Architecture: BAG3D Integration

## Overview

GISKit integreert de **3DBAG API** (api.3dbag.nl) als externe service via de PDOK provider. Hoewel BAG3D niet door PDOK wordt gehost, is het opgenomen in de PDOK provider voor gebruiksgemak.

## Data Sources Architecture

### 1. PDOK Services (api.pdok.nl)

**WFS Protocol:**
- **BAG** (Basisregistratie Adressen en Gebouwen)
  - Protocol: WFS 2.0
  - Format: GeoJSON
  - Layers: `pand`, `verblijfsobject`

- **BRK** (Kadaster)
  - Protocol: WFS 2.0
  - Format: GeoJSON
  - Layers: `perceel`, `kadastrale_grens`, `bebouwing`, etc.

**OGC API Features:**
- **BGT** (Basisregistratie Grootschalige Topografie)
  - Protocol: OGC API Features
  - Format: GeoJSON
  - Layers: 46 topografische lagen (pand, wegdeel, waterdeel, etc.)

### 2. External Services (NOT from PDOK)

**3DBAG API (api.3dbag.nl):**
- **BAG3D** (3D Gebouwmodellen)
  - Protocol: OGC API Features-like interface
  - Format: **CityJSON** (niet GeoJSON!)
  - Host: api.3dbag.nl (NIET api.pdok.nl)
  - Collection: `pand` (bevat alle LODs)
  - LODs: 0, 1.2, 1.3, 2.2

## CityJSON Format

### Structuur

Normale GeoJSON:
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

1. **Geen top-level geometry** - geometrie zit in CityObjects
2. **Vertices array** - coördinaten zijn indices in gedeelde array
3. **Multiple LODs** - meerdere detail niveaus per gebouw
4. **Type hierarchy** - Building (parent) en BuildingPart (children)

## ⚠️ CRITICAL: CityJSON 2.0 Transform (PER-PAGE!)

**WAARSCHUWING**: Dit is de meest kritieke aspect van BAG3D integratie!

### Het Probleem

CityJSON 2.0 gebruikt **per-page transforms** voor vertex compressie:

1. **Vertices zijn INTEGER arrays**, niet float coördinaten
2. **Elke pagination pagina heeft ZIJN EIGEN transform** in `metadata.transform`
3. **Transform MOET toegepast worden**: `real_coord = vertex * scale + translate`
4. **Verkeerde transform = verkeerde coördinaten** (kilometers offset!)

### Voorbeeld Transform

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

Correcte transformatie:
```python
# Vertex: [5455, 661895, 5567]
x = 5455 * 0.001 + 80113.570 = 80119.025 (RD coördinaat)
y = 661895 * 0.001 + 429309.435 = 430971.330 (RD coördinaat)
z = 5567 * 0.001 + (-1.302) = 4.265 (hoogte in meters)
```

**ZONDER transform**: je zou [5455, 661895] als coördinaten gebruiken → compleet verkeerde locatie!

### Walking Grid & Multi-Page Downloads

Bij het downloaden van grote gebieden:
- API retourneert meerdere pagina's (pagination)
- **Elke pagina heeft verschillende transform**
- Features van verschillende pagina's moeten correct samengevoegd worden
- **ELKE feature moet met ZIJN EIGEN page transform worden getransformeerd**

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

### Vergelijking met Sitedb

Sitedb implementatie (correct):
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

GISKit implementatie (ook correct, maar anders):
```python
# Process each page immediately with its transform
for page in pages:
    page_transform = page['metadata']['transform']
    gdf = cityjson_to_geodataframe(page, transform=page_transform)
    all_gdfs.append(gdf)  # Already transformed to real coordinates

# Combine all GeoDataFrames (coordinates already correct)
combined = gpd.concat(all_gdfs)
```

### Verificatie

Test dat transform correct werkt:
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

- **LOD 0**: 2D voetprint (polygon)
  - Source: `Building` object
  - Geometry: MultiSurface met XY coördinaten
  
- **LOD 1.2**: Simpel 3D blok met plat dak
  - Source: `BuildingPart` object
  - Geometry: Solid met XYZ coördinaten

- **LOD 1.3**: 3D blok met dak geometrie
  - Source: `BuildingPart` object
  - Geometry: Solid met XYZ coördinaten

- **LOD 2.2**: Gedetailleerd 3D model (dak details)
  - Source: `BuildingPart` object
  - Geometry: Solid met XYZ coördinaten
  - Attributes: volume_lod22, daktype, etc.

### Layer Mapping

Recipe request:
```json
{
  "service": "bag3d",
  "layers": ["pand", "lod22"]
}
```

Hoe het werkt:
1. `pand` → downloadt "pand" collection, parsed als LOD 0 (2D)
2. `lod22` → downloadt "pand" collection, parsed als LOD 2.2 (3D)

API call voor beide:
```
GET https://api.3dbag.nl/collections/pand/items?bbox=...
```

Parser detectie (in `ogc_features.py`):
```python
if collection_id.startswith("lod"):
    lod_num = collection_id[3:]  # "lod22" → "22"
    lod = f"{lod_num[0]}.{lod_num[1]}"  # "22" → "2.2"
else:
    lod = "0"  # Default: footprint

# Alle LODs komen uit dezelfde API response!
gdf = cityjson_to_geodataframe(geojson, lod=lod)
```

## Implementation Details

### Files Modified

1. **giskit/protocols/cityjson.py** (NEW)
   - CityJSON parser voor 3DBAG API
   - Extraheert LOD 0 uit Building objects
   - Extraheert LOD 1.2/1.3/2.2 uit BuildingPart objects
   - Converteert vertices + boundaries naar Shapely geometrie

2. **giskit/protocols/ogc_features.py**
   - Detecteert CityJSON format (kijkt naar "CityObjects")
   - Herkent LOD layers (lod22, lod12, etc.)
   - Mapped lod* layers naar "pand" collection
   - Geeft LOD parameter door aan CityJSON parser

3. **giskit/providers/pdok.py**
   - Registreert bag3d als externe service
   - URL: https://api.3dbag.nl (niet api.pdok.nl!)
   - Format: cityjson (niet geojson!)
   - Special handling voor LOD layers

4. **giskit/cli/main.py**
   - Voegt _metadata layer toe aan GeoPackage output
   - Bevat: adres, centrum punt, bbox, datum, CRS

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

# Resulteert in 2 layers:
# - bag3d_pand: 2D footprints (LOD 0)
# - bag3d_lod22: 3D models (LOD 2.2) met Z-coördinaten
```

## Output Structure

```
site_underlegger.gpkg
├── _metadata (1 feature)
│   └── adres, x, y, radius, bbox, datum, crs
│
├── bag_pand (23 features)
├── bag_verblijfsobject (38 features)
│
├── bag3d_pand (23 features)         ← LOD 0: 2D footprints
├── bag3d_lod22 (23 features)        ← LOD 2.2: 3D models met Z
│
├── brk_Perceel (52 features)
├── brk_KadastraleGrens (152 features)
└── bgt_* (26 layers, 1330 features)
```

## Key Insights

1. **BAG3D ≠ PDOK**: Externe service, andere host, ander format
2. **CityJSON ≠ GeoJSON**: Vertices array + boundaries ipv coordinates
3. **LOD = Virtual Layers**: Alle LODs in 1 API response, split in parser
4. **Building vs BuildingPart**: Parent heeft footprint, child heeft 3D
5. **Z-coordinates**: LOD 2.2 heeft echte 3D geometrie (MultiPolygon met Z)

## Performance Note

Omdat alle LODs in dezelfde API response zitten, worden bij het downloaden van
meerdere LODs dezelfde features meerdere keren opgehaald. Voor optimale 
performance zou je 1x kunnen downloaden en lokaal splitsen, maar de huidige
implementatie is eenvoudiger en volgt het layer-based design pattern.
