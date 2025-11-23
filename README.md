# GISKit

**Recipe-driven spatial data downloader for Netherlands geo-data**

[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-110%20passing-brightgreen.svg)](tests/)

---

## What is GISKit?

GISKit is a Python tool for downloading Dutch spatial data using simple JSON "recipes". Define what data you need and where you need it - GISKit handles the downloads and combines everything into a single GeoPackage.

**Perfect for:**
- Creating project underlays for construction/infrastructure projects
- Downloading base maps for GIS analysis
- Collecting spatial context data for locations
- Automating repetitive spatial data downloads

### Key Features

- **Recipe-Driven**: Define your data needs in simple JSON
- **PDOK Integration**: Access to 50+ Dutch government spatial datasets
- **Smart Downloads**: Automatic bbox calculation from addresses
- **Single Output**: Everything combined in one GeoPackage
- **CRS Handling**: Automatic coordinate transformation
- **Export Options**: GeoPackage, GeoJSON, CityJSON, optional IFC/GLB


## Quick Start

### Installation

**From PyPI (recommended):**
```bash
pip install giskit

# With IFC export support (Python 3.10-3.12 only)
pip install giskit[ifc]
```

**From source:**
```bash
git clone https://github.com/sanderboer/py-giskit.git
cd py-giskit
pip install -e .
```

### Your First Recipe

Create `dam_square.json`:

```json
{
  "name": "Dam Square Buildings",
  "location": {
    "type": "address",
    "value": "Dam 1, Amsterdam",
    "radius": 500
  },
  "datasets": [
    {
      "provider": "pdok",
      "service": "bgt",
      "layers": ["pand", "wegdeel"]
    }
  ],
  "output": {
    "path": "./dam_square.gpkg",
    "crs": "EPSG:28992"
  }
}
```

Run it:

```bash
giskit run dam_square.json
```

Result: `dam_square.gpkg` with buildings and roads around Dam Square!


## Recipe Examples

All examples are in the `recipes/` directory. Try them out:

```bash
# Download buildings and infrastructure around Curieweg, Spijkenisse
giskit run recipes/curieweg_multi_service.json

# Amsterdam Dam Square with buildings
giskit run recipes/amsterdam_dam_square.json

# Simple bbox example
giskit run recipes/bbox_simple.json
```

### Urban Planning Dataset

Comprehensive data for a project location:

```json
{
  "name": "Curieweg Project Underlay",
  "location": {
    "type": "address",
    "value": "Curieweg 7a, Spijkenisse",
    "radius": 1000
  },
  "datasets": [
    {"provider": "pdok", "service": "bgt", "layers": ["pand", "wegdeel", "waterdeel"]},
    {"provider": "pdok", "service": "bag", "layers": ["pand", "verblijfsobject"]},
    {"provider": "pdok", "service": "cbs-wijken-buurten-2024", "layers": ["buurten"]},
    {"provider": "pdok", "service": "bestuurlijkegebieden", "layers": ["gemeenten"]}
  ],
  "output": {
    "path": "./curieweg.gpkg",
    "crs": "EPSG:28992"
  }
}
```

### Location Types

**Address with buffer:**
```json
{
  "location": {
    "type": "address",
    "value": "Curieweg 7a, Spijkenisse",
    "radius": 1000
  }
}
```

**Point coordinates:**
```json
{
  "location": {
    "type": "point",
    "value": [4.89, 52.37],
    "crs": "EPSG:4326",
    "radius": 500
  }
}
```

**Bounding box:**
```json
{
  "location": {
    "type": "bbox",
    "value": [120700, 487000, 120950, 487250],
    "crs": "EPSG:28992"
  }
}
```


## Available Data Sources

### PDOK (Platform Digitale Overheid - Netherlands)

GISKit provides access to **50+ Dutch government datasets** via PDOK's OGC API Features:

**Base Registries (Basisregistraties):**
- **BGT** - Large Scale Topography (54 layers: buildings, roads, water, terrain, etc.)
- **BAG** - Buildings and Addresses (buildings, addresses, residence objects)
- **BAG3D** - 3D Building Models (LoD 1.2, 1.3, 2.2 in CityJSON format)
- **BRK** - Cadastral Parcels

**Infrastructure:**
- **NWB Roads** - National Road Database (road segments, junctions)
- **NWB Waterways** - Waterway network

**Statistics & Administration:**
- **CBS Neighborhoods 2024** - Statistical areas (neighborhoods, districts, municipalities)
- **Administrative Boundaries** - Municipalities, provinces, water boards

**Environment:**
- **Protected Areas** - Nature reserves, Natura 2000
- **Soil Data** - Soil types, contamination

See [PDOK_SERVICES.md](PDOK_SERVICES.md) for complete catalog with all layers.

### Planned Providers

- **OpenStreetMap** - Global POI, buildings, roads via Overpass API
- **AHN Elevation** - Dutch elevation data via WCS
- **Aerial Imagery** - Luchtfoto via WMTS


## CLI Commands

**Run recipes:**
```bash
# Execute a recipe
giskit run recipe.json

# Validate recipe syntax
giskit recipe validate recipe.json
```

**Explore providers:**
```bash
# List available providers and services
giskit providers list

# Show PDOK service details
giskit providers info pdok

# Search for specific data
giskit search "buildings"
```

**Monitor API quirks:**
```bash
# Show known API quirks for providers
giskit quirks list

# Show details for specific provider
giskit quirks show pdok ogc-features

# Monitor which quirks are being applied
giskit quirks monitor
```

## Export Formats

**Built-in formats:**
- GeoPackage (`.gpkg`) - default, recommended
- GeoJSON (`.geojson`)
- Shapefile (`.shp`)
- CityJSON (`.json`) - for 3D data

**Optional IFC/GLB export:**

Requires `pip install giskit[ifc]` (Python 3.10-3.12 only)

```bash
# Export GeoPackage to IFC
giskit export ifc data.gpkg output.ifc

# Convert IFC to GLB (for web viewers)
giskit export glb data.ifc output.glb
```

See [EXPORT_GUIDE.md](EXPORT_GUIDE.md) for details.


## How It Works

1. **Define** - Write a JSON recipe with location and datasets
2. **Geocode** - GISKit converts addresses to coordinates
3. **Download** - Fetches data from PDOK OGC API Features
4. **Transform** - Converts to target CRS if needed
5. **Combine** - Merges all layers into single GeoPackage

```
┌──────────────┐
│ JSON Recipe  │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────┐
│  Geocoding   │─────▶│ PDOK Lookup │
└──────┬───────┘      └─────────────┘
       │
       ▼
┌──────────────┐
│   Download   │──────┬────────────────┐
└──────┬───────┘      │                │
       │         ┌────▼────┐      ┌────▼────┐
       │         │  BGT    │      │   BAG   │
       │         │ (54 lyr)│      │ (3 lyr) │
       │         └────┬────┘      └────┬────┘
       ▼              │                │
┌──────────────┐      │                │
│  Transform   │◀─────┴────────────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ GeoPackage   │
│ (.gpkg)      │
└──────────────┘
```

## Project Structure

```
giskit/
├── cli/              # Command-line interface
├── core/             # Recipe parsing, geocoding, spatial ops
├── protocols/        # OGC Features, WMTS, WCS protocols
├── providers/        # PDOK, OSM provider implementations
├── exporters/        # IFC/GLB export (optional)
└── config/           # YAML configurations for services

recipes/              # Example recipes ready to use
tests/                # 110+ unit and integration tests
```


## Development

### Running Tests

```bash
# All tests (110 passing)
pytest

# With coverage report
pytest --cov=giskit --cov-report=html

# Specific test suites
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Lint code
ruff check .

# Format code
ruff format .
```

## Documentation

- **[PDOK_SERVICES.md](PDOK_SERVICES.md)** - Complete PDOK service catalog
- **[EXPORT_GUIDE.md](EXPORT_GUIDE.md)** - IFC/GLB export instructions
- **[QUIRKS_SYSTEM.md](QUIRKS_SYSTEM.md)** - API compatibility handling
- **[PLAN.md](PLAN.md)** - Project roadmap
- **[ARCHITECTURE_BAG3D.md](ARCHITECTURE_BAG3D.md)** - 3D data handling

## Use Cases

**Urban Planning:**
- Project site context data (buildings, infrastructure, parcels)
- Statistical area boundaries for reports
- Base maps for presentations

**Construction:**
- Site underlay generation
- Existing infrastructure mapping
- Environmental constraints (protected areas, water)

**GIS Analysis:**
- Batch download base data for multiple locations
- Standardized data collection workflows
- Automated updates of project data

**Research:**
- Reproducible spatial data downloads
- Consistent data collection methodology
- Share data requirements via recipes


## Contributing

Contributions welcome! This project is in active development.

1. Check [PLAN.md](PLAN.md) for current priorities
2. Create an issue for discussion
3. Submit a pull request

## Credits

**Built with:**
- [GeoPandas](https://geopandas.org/) - Spatial data handling
- [Shapely](https://shapely.readthedocs.io/) - Geometry operations
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation

**Data sources:**
- [PDOK](https://www.pdok.nl/) - Dutch government spatial data platform
- [Nominatim](https://nominatim.org/) - OpenStreetMap geocoding

## License

MIT License - See [LICENSE](LICENSE)

---

**Made by A190**

*Simple recipes for Dutch spatial data*
