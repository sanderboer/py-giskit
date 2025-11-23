# GISKit Recipe Examples

This directory contains example recipe files demonstrating different use cases.

## Examples

### 1. `amsterdam_dam_square.json`
**Use case:** Download buildings and restaurants near a specific address

Features demonstrated:
- Address-based location with radius
- Multiple datasets from different providers (PDOK + OSM)
- Custom output CRS (RD New - EPSG:28992)
- Layer prefix for organization
- Metadata tracking

**CLI usage:**
```bash
giskit run recipes/amsterdam_dam_square.json
```

### 2. `bbox_simple.json`
**Use case:** Download data for a specific bounding box

Features demonstrated:
- Direct bounding box specification (WGS84)
- Multiple layers from single provider
- WGS84 output (default)
- Overwrite protection (overwrite: false)

**CLI usage:**
```bash
giskit run recipes/bbox_simple.json
```

### 3. `point_with_radius.json`
**Use case:** Download data around a coordinate

Features demonstrated:
- Point location with radius (1km buffer)
- Multiple services from same provider
- RD New output CRS

**CLI usage:**
```bash
giskit run recipes/point_with_radius.json
```

## Recipe Structure

All recipes follow this structure:

```json
{
  "name": "Human-readable name",
  "description": "What this recipe does",
  "location": {
    "type": "address|point|bbox|polygon",
    "value": "...",
    "radius": 500,
    "crs": "EPSG:4326"
  },
  "datasets": [
    {
      "provider": "pdok|osm|copernicus|...",
      "service": "bgt|bag|...",
      "layers": ["layer1", "layer2"],
      "query": "...",
      "product": "...",
      "extra": {}
    }
  ],
  "output": {
    "path": "./output.gpkg",
    "format": "gpkg|geojson|shp|fgb",
    "crs": "EPSG:4326",
    "overwrite": true|false,
    "layer_prefix": "prefix_"
  },
  "metadata": {}
}
```

## Location Types

1. **address**: Geocode address → buffer by radius
2. **point**: [lon, lat] → buffer by radius
3. **bbox**: [minx, miny, maxx, maxy]
4. **polygon**: [[lon, lat], ...]

## Supported Providers (Planned)

- **pdok**: Netherlands (BGT, BAG, BAG3D, BRK, AHN)
- **osm**: Global (Overpass API)
- **copernicus**: EU (DEM, Land Cover, etc.)
- **usgs**: USA (NAIP, NED, etc.)

## Validation

Test recipe validity without downloading:

```bash
giskit validate recipes/amsterdam_dam_square.json
```

## Creating Your Own Recipes

1. Copy an example that's closest to your use case
2. Modify the location to your area of interest
3. Update datasets to match your data needs
4. Adjust output path and CRS
5. Validate before running:
   ```bash
   giskit validate my_recipe.json
   giskit run my_recipe.json
   ```

## Tips

- Use `radius: 500` for small areas (street-level)
- Use `radius: 5000` for neighborhoods
- Use `bbox` for rectangular areas
- Use `address` for geocoding (human-readable)
- Set `overwrite: true` for development/testing
- Set `overwrite: false` for production (safety)
- Use `layer_prefix` to organize multi-recipe outputs
