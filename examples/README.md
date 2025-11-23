# GISKit Examples

This directory contains ready-to-use examples for downloading Dutch spatial data with GISKit.

## Site Underlegger (Complete Site Base Map)

Build a complete Dutch site "underlegger" (base map) with one command, equivalent to Sitedb's `make site-underlegger`.

### What's Included

The site underlegger contains:
- **BAG pand** - Building footprints
- **BRK perceel** - Cadastral parcels
- **BAG 3D LOD 2.2** - 3D building models with roof geometry
- **BGT complete** - All 46 topographic layers:
  - Buildings, roads, water, vegetation, terrain
  - Infrastructure, street furniture, administrative boundaries
  - Line features (kerbs, fences, etc.)
  - Point features (poles, trees, sensors, etc.)
- **_metadata layer** - Location info, bbox, timestamp, CRS

### Quick Start

```bash
# Download complete site for an address
cd giskit/examples
./build_site_underlegger.sh "Dam 1, Amsterdam" 500

# Custom output location
./build_site_underlegger.sh "Curieweg 7a, Spijkenisse" 500 ../data/curieweg.gpkg

# Use coordinates (RD)
./build_site_underlegger.sh "155000,463000" 200

# Use coordinates (WGS84 lat,lon from Google Maps)
./build_site_underlegger.sh "52.37,4.89" 300
```

### Output

The script creates a GeoPackage with:
- All requested layers in RD New (EPSG:28992)
- Proper layer naming (e.g., `bgt_wegdeel`, `bag_pand`, `brk_perceel`)
- Metadata layer with location information
- Typically 20-50 MB for 500m radius area

### View the Data

**In QGIS:**
```bash
qgis site_underlegger.gpkg
```

**In Python:**
```python
import geopandas as gpd

# List all layers
layers = gpd.list_layers('site_underlegger.gpkg')
print(layers)

# Read specific layer
roads = gpd.read_file('site_underlegger.gpkg', layer='bgt_wegdeel')
buildings = gpd.read_file('site_underlegger.gpkg', layer='bag3d_lod22')
parcels = gpd.read_file('site_underlegger.gpkg', layer='brk_perceel')

# Check metadata
metadata = gpd.read_file('site_underlegger.gpkg', layer='_metadata')
print(metadata)
```

## Recipe Files

### `site_underlegger.json`

Template recipe for complete site downloads. The shell script automatically customizes:
- Location (address or coordinates)
- Radius
- Output filename

You can also use this recipe directly with custom locations:

```bash
# Edit the recipe JSON to set your location
nano site_underlegger.json

# Execute the recipe
giskit execute site_underlegger.json --output mysite.gpkg
```

## Comparison with Sitedb

This GISKit approach is equivalent to Sitedb's workflow:

**Sitedb (old):**
```bash
cd Sitedb
make db-init DB_FILE=../data/site.gpkg
make download-bag DB_FILE=../data/site.gpkg ADDRESS="Dam 1, Amsterdam" RADIUS=500
make download-brk DB_FILE=../data/site.gpkg ADDRESS="Dam 1, Amsterdam" RADIUS=500
make download-bag3d DB_FILE=../data/site.gpkg ADDRESS="Dam 1, Amsterdam" RADIUS=500
make download-bgt DB_FILE=../data/site.gpkg ADDRESS="Dam 1, Amsterdam" RADIUS=500
```

**GISKit (new):**
```bash
cd giskit/examples
./build_site_underlegger.sh "Dam 1, Amsterdam" 500
```

### Advantages

1. **Single command** - No need for multiple steps
2. **No database initialization** - Automatic
3. **Flexible input** - Address, RD coords, or WGS84 coords
4. **Recipe-based** - Easy to customize and version control
5. **Parallel downloads** - Faster execution
6. **Better error handling** - Clear feedback
7. **Automatic CRS handling** - No manual transformation needed

## Advanced Usage

### Customize the Recipe

Create your own recipe variants:

```bash
# Copy the template
cp site_underlegger.json my_custom_site.json

# Edit to include only specific layers
nano my_custom_site.json

# Execute
giskit execute my_custom_site.json --output custom.gpkg
```

### Export to IFC

Once you have the GeoPackage, export to IFC:

```bash
# Export all layers
giskit export ifc site_underlegger.gpkg --output site.ifc

# Export specific layers
giskit export ifc site_underlegger.gpkg \
  --layers bgt_wegdeel,bgt_waterdeel,bag3d_lod22 \
  --output site_roads_water_buildings.ifc

# Export without buildings (onderlegger only)
giskit export ifc site_underlegger.gpkg \
  --exclude-layers bag_pand,bgt_pand,bag3d_lod12,bag3d_lod13,bag3d_lod22 \
  --output onderlegger.ifc
```

## Layer Details

### BAG Layers
- `bag_pand` - Building footprints with BAG identifiers

### BRK Layers
- `brk_perceel` - Cadastral parcels with ownership information

### BAG 3D Layers
- `bag3d_lod22` - 3D building models with roof geometry (recommended)
  - Includes roof shapes, dormers, overhangs
  - LOD 2.2 is most detailed publicly available

### BGT Layers (46 total)

**Main Features:**
- `bgt_pand` - Buildings
- `bgt_wegdeel` - Roads and paths
- `bgt_waterdeel` - Water bodies
- `bgt_begroeidterreindeel` - Vegetation areas
- `bgt_onbegroeidterreindeel` - Bare terrain

**Supporting Features:**
- `bgt_ondersteunendwegdeel` - Curbs, traffic islands
- `bgt_ondersteunendwaterdeel` - Banks, quays
- `bgt_overbruggingsdeel` - Bridges
- `bgt_tunneldeel` - Tunnels
- `bgt_kunstwerkdeel_*` - Engineering structures

**Objects:**
- `bgt_paal` - Poles
- `bgt_put` - Manholes, drains
- `bgt_bord` - Signs
- `bgt_straatmeubilair` - Street furniture
- `bgt_vegetatieobject_*` - Trees, bushes

**Administrative:**
- `bgt_openbareruimtelabel` - Street names
- `bgt_buurt`, `bgt_wijk`, `bgt_stadsdeel` - Neighborhoods, districts
- `bgt_pand_nummeraanduiding` - Building addresses

## Requirements

- Python 3.9+
- GISKit installed (`pip install giskit` or `poetry install`)
- Internet connection for PDOK data access
- `jq` for JSON manipulation (install: `brew install jq` on macOS)

## Troubleshooting

### Script fails with "giskit: command not found"

The script will automatically try `python -m giskit.cli.main` as fallback. Alternatively, activate your environment:

```bash
# If using poetry
poetry shell

# If using venv
source venv/bin/activate

# Then run the script
./build_site_underlegger.sh "Dam 1, Amsterdam" 500
```

### Large radius takes too long

For large areas (radius > 1000m), consider:
1. Reducing the radius
2. Downloading specific BGT layers only
3. Running during off-peak hours
4. Using the recipe directly with layer filters

### Location not found

Make sure your address or coordinates are valid:
- **Addresses**: Include city name (e.g., "Dam 1, Amsterdam", not just "Dam 1")
- **RD coordinates**: Must be in Netherlands (X: 0-300000, Y: 300000-625000)
- **WGS84 coordinates**: Format as lat,lon (e.g., "52.37,4.89")

### "jq: command not found"

Install jq for JSON manipulation:

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Or manually edit the recipe JSON file
```

## Support

For issues or questions:
1. Check the [main GISKit README](../README.md)
2. Review [CODE_REVIEW.md](../CODE_REVIEW.md) for architecture details
3. See [CRS_HANDLING.md](../CRS_HANDLING.md) for coordinate system info

## License

Same as GISKit main project.
