# 🌍 GISKit

**Recipe-driven spatial data downloader for any location, any provider, anywhere**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Pre-Alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)](https://github.com/a190/giskit)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 What is GISKit?

GISKit is a **protocol-agnostic spatial data downloader** that uses JSON "recipes" to fetch curated datasets from multiple providers worldwide. Download vector and raster data from OGC-compliant services (WFS, WMTS, OGC Features) and package everything into a single GeoPackage.

### Key Features

- 📜 **Recipe-Driven**: Define your data needs in JSON
- 🌐 **Multi-Provider**: PDOK, OpenStreetMap, Copernicus, USGS, and more
- 🔌 **Protocol-Agnostic**: OGC Features, WMTS, WCS, Overpass API
- 📦 **Single Output**: Everything in one GeoPackage file
- 🗺️ **CRS Support**: Automatic coordinate transformation
- 🚀 **Async Downloads**: Fast parallel fetching
- 🧩 **Extensible**: Plugin system for custom providers

---

## 🚀 Quick Start

### Installation

```bash
# From PyPI (when published)
pip install giskit

# With IFC export support
pip install giskit[ifc]

# Development installation from source
git clone https://github.com/a190/giskit.git
cd giskit
pip install -e .

# Or using poetry
poetry install
```

### IfcConvert for GLB Export

For GLB export functionality, you need IfcConvert. See [EXPORT_GUIDE.md](EXPORT_GUIDE.md) for details.

```bash
# Option 1: Install via conda (recommended)
conda install -c ifcopenshell ifcopenshell

# Option 2: Install via pip
pip install ifcopenshell

# Option 3: Manual binary download
# See EXPORT_GUIDE.md for platform-specific instructions
```

### Your First Recipe

Create `amsterdam.json`:

```json
{
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
    "path": "./amsterdam.gpkg"
  }
}
```

Run the recipe:

```bash
giskit run amsterdam.json
```

Result: `amsterdam.gpkg` with buildings and roads around Dam square!

---

## 📖 Example Recipes

### Dutch Urban Planning Dataset

```json
{
  "location": {
    "type": "address",
    "value": "Curieweg 7a, Spijkenisse",
    "radius": 1000
  },
  "datasets": [
    {"provider": "pdok", "service": "bgt", "layers": ["pand", "wegdeel"]},
    {"provider": "pdok", "service": "bag3d", "layers": ["lod22"]},
    {"provider": "pdok", "service": "brk", "layers": ["perceel"]},
    {"provider": "osm", "query": "amenity=*"}
  ],
  "output": {
    "path": "./spijkenisse.gpkg",
    "crs": "EPSG:28992"
  }
}
```

### Global OpenStreetMap POI

```json
{
  "location": {
    "type": "point",
    "value": [4.89, 52.37],
    "crs": "EPSG:4326",
    "radius": 2000
  },
  "datasets": [
    {
      "provider": "osm",
      "query": "amenity IN ('restaurant', 'cafe', 'bar')"
    }
  ]
}
```

### Elevation + Aerial Imagery

```json
{
  "location": {
    "type": "bbox",
    "value": [120700, 487000, 120950, 487250],
    "crs": "EPSG:28992"
  },
  "datasets": [
    {"provider": "pdok-wcs", "service": "ahn.dtm", "product": "dtm", "resolution": 1},
    {"provider": "pdok-wcs", "service": "ahn.dsm", "product": "dsm", "resolution": 1},
    {"provider": "pdok-wmts", "service": "luchtfoto.actueel_25cm"}
  ]
}
```

---

## 🏗️ Architecture

```
┌─────────────┐
│   Recipe    │  JSON definition of data requirements
│   (JSON)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Downloader │  Orchestrates the entire process
└──────┬──────┘
       │
       ├──────────────┬──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Protocol │   │ Protocol │   │ Protocol │   │ Protocol │   │ Protocol │
│OGC Feat. │   │  WMTS    │   │   WCS    │   │Overpass  │   │   ...    │
└─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘
      │              │              │              │              │
      ▼              ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Provider │   │ Provider │   │ Provider │   │ Provider │   │ Provider │
│   PDOK   │   │   PDOK   │   │   PDOK   │   │   OSM    │   │   USGS   │
│  Vector  │   │  Tiles   │   │Elevation │   │          │   │          │
└─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘
      │              │              │              │              │
      └──────────────┴──────────────┴──────────────┴──────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ GeoPackage  │  Single output file (vector)
              │   (.gpkg)   │  + GeoTIFF (raster)
              └─────────────┘
```

---

## 📋 CLI Commands

```bash
# Execute a recipe
giskit run recipe.json

# Validate recipe syntax
giskit recipe validate recipe.json

# Create recipe from template
giskit recipe create --template urban --location "Amsterdam" --output recipe.json

# List available providers
giskit providers list
giskit providers list --country NL

# Show provider details
giskit providers info pdok

# Scan provider capabilities
giskit index scan https://api.pdok.nl --output pdok.json

# Search for layers
giskit search "buildings" --provider pdok
```

---

## 🌐 Supported Providers

### Current (Production Ready)
- ✅ **PDOK** (Netherlands) - **53 services** across 11 categories
  - **Vector Data (OGC Features)**: BGT (54 layers), BAG, BRK, BAG3D, CBS statistics, NWB roads/waterways
  - **Aerial Imagery (WMTS)**: Luchtfoto (6 layers), Satellietbeeld (3 layers), BRT Achtergrondkaart (4 layers)
  - **Elevation Data (WCS)**: AHN4 (DTM/DSM at 0.5m resolution)
  - 📖 [Complete PDOK Services Overview](PDOK_SERVICES_OVERVIEW.md)

### Planned
- 🔄 **OpenStreetMap** (Global) - Overpass API for POI, buildings, roads
- 🔄 **Copernicus** (EU) - Satellite imagery, land cover
- 🔄 **USGS** (USA) - National Map, elevation, hydrography
- 🔄 **Nominatim** (Global) - Geocoding service
- 🔄 **Natural Earth** (Global) - Base maps

---

## 🔧 Development Status

**Current Version**: 0.1.0-dev (Pre-Alpha)

### Roadmap

- **Week 1**: ✅ Project structure + Recipe schema
- **Week 2**: Recipe parser + validator
- **Week 3**: PDOK OGC Features integration
- **Week 4**: OpenStreetMap Overpass support
- **Week 5**: WMTS raster support (elevation, aerial)
- **Week 6**: Provider indexer/scanner
- **Week 7-8**: Polish + Beta release

See [PLAN.md](PLAN.md) for detailed roadmap.

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=giskit --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

---

## 📚 Documentation

- [PDOK Services Catalog](PDOK_SERVICES.md) - Complete list of 40+ PDOK services
- [Getting Started Guide](docs/getting-started.md) *(coming soon)*
- [Recipe Reference](docs/recipes.md) *(coming soon)*
- [Provider Guide](docs/providers.md) *(coming soon)*
- [Protocol Guide](docs/protocols.md) *(coming soon)*
- [API Reference](docs/api-reference.md) *(coming soon)*

---

## 🤝 Contributing

GISKit is in active development. Contributions welcome!

1. Check [PLAN.md](PLAN.md) for current priorities
2. Create an issue for discussion
3. Submit a pull request

---

## 🙏 Credits

**Built on the shoulders of giants:**
- [GeoPandas](https://geopandas.org/) - Spatial data handling
- [Shapely](https://shapely.readthedocs.io/) - Geometry operations
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation

**Inspired by:**
- **Sitedb** - Dutch project underlay generator (sister project)
- **QGIS** - The gold standard for desktop GIS
- **OWSLib** - Python OGC web services library

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🔗 Related Projects

- **[Sitedb](../Sitedb/)** - Dutch spatial data downloader (PDOK-specific)
- **[OWSLib](https://github.com/geopython/OWSLib)** - Python OGC client library
- **[pyogrio](https://github.com/geopandas/pyogrio)** - Fast vector I/O

---

**Made with ❤️ by A190**

*Download spatial data, anywhere in the world, with a simple JSON recipe.*
