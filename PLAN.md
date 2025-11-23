# 🌍 GISKit Development Plan

**Tagline:** *Recipe-driven spatial data downloader for any location, any provider, anywhere*

**Status:** Pre-Alpha Development  
**Version:** 0.1.0-dev  
**Created:** 2025-01-22  
**Location:** `/Users/Mauc/A190-sitedb/giskit/`

---

## 📋 Project Vision

GISKit is een protocol-agnostische spatial data downloader die met JSON "recipes" bouquets van ruimtelijke data verzamelt rond elk punt wereldwijd, van elke OGC-compliant provider.

### Key Differentiators vs Sitedb
- **Sitedb**: Nederlandse projectonderleggers (PDOK-specifiek, hardcoded)
- **GISKit**: Internationale data bouquets (multi-provider, recipe-driven)

---

## 🎯 Core Principles

1. **Recipe-Driven**: Declaratieve configuratie in JSON
2. **Protocol-Agnostic**: WFS, WMTS, OGC Features, XYZ tiles, Overpass
3. **Provider-Neutral**: Werkt met PDOK, OSM, USGS, Copernicus
4. **International**: Niet beperkt tot Nederland
5. **Extensible**: Plugin systeem voor providers/protocols

---

## 🏗️ Project Structure

```
giskit/
├── PLAN.md                         # This file
├── README.md                       # Project overview
├── pyproject.toml                  # Package configuration
├── .gitignore                      # Git ignore rules
│
├── giskit/                         # Main Python package
│   ├── __init__.py
│   ├── __version__.py
│   │
│   ├── core/                       # Core functionality
│   │   ├── __init__.py
│   │   ├── recipe.py              # Recipe parser/validator
│   │   ├── downloader.py          # Main orchestrator
│   │   ├── geocoder.py            # Multi-provider geocoding
│   │   ├── transformer.py         # CRS transformations
│   │   └── database.py            # GeoPackage writer
│   │
│   ├── protocols/                  # Protocol implementations
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract Protocol class
│   │   ├── ogc_features.py        # OGC API Features
│   │   ├── wfs.py                 # WFS 2.0/3.0
│   │   ├── wmts.py                # WMTS raster tiles
│   │   ├── wms.py                 # WMS raster service
│   │   ├── xyz.py                 # XYZ tiles
│   │   └── overpass.py            # OSM Overpass API
│   │
│   ├── providers/                  # Provider-specific code
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract Provider class
│   │   ├── pdok.py                # PDOK (Netherlands)
│   │   ├── osm.py                 # OpenStreetMap
│   │   ├── nominatim.py           # Nominatim geocoding
│   │   └── registry.py            # Provider registry loader
│   │
│   ├── indexer/                    # API capability scanner
│   │   ├── __init__.py
│   │   ├── scanner.py             # Capability scanner
│   │   ├── parsers.py             # XML/JSON parsers
│   │   └── cache.py               # Cache manager
│   │
│   ├── cli/                        # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py                # Main CLI entry (Typer)
│   │   ├── run.py                 # Execute recipes
│   │   ├── recipe.py              # Recipe commands
│   │   ├── providers.py           # Provider commands
│   │   └── index.py               # Indexer commands
│   │
│   └── utils/                      # Shared utilities
│       ├── __init__.py
│       ├── validation.py          # Pydantic validators
│       ├── logging.py             # Logging config
│       └── progress.py            # Progress bars (rich)
│
├── recipes/                        # Recipe examples
│   ├── schemas/
│   │   └── recipe-v1.0.json       # JSON Schema definition
│   ├── examples/
│   │   ├── nl_urban_planning.json
│   │   ├── nl_environmental.json
│   │   ├── osm_amenities.json
│   │   └── eu_elevation.json
│   └── templates/
│       ├── urban.json
│       ├── environmental.json
│       └── infrastructure.json
│
├── providers/                      # Provider capability definitions
│   ├── index.json                 # Master provider index
│   ├── pdok.json                  # PDOK capabilities
│   ├── osm.json                   # OSM capabilities
│   └── nominatim.json             # Nominatim geocoding
│
├── tests/                          # Test suite
│   ├── unit/
│   │   ├── test_recipe.py
│   │   ├── test_protocols/
│   │   ├── test_providers/
│   │   └── test_geocoding.py
│   ├── integration/
│   │   ├── test_pdok_integration.py
│   │   ├── test_osm_integration.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── recipes/
│       ├── capabilities/
│       └── mock_responses/
│
├── docs/                           # Documentation
│   ├── index.md
│   ├── getting-started.md
│   ├── recipes.md
│   ├── providers.md
│   ├── protocols.md
│   └── api-reference.md
│
└── examples/                       # Working examples
    ├── simple_pdok.py
    ├── osm_poi.py
    └── multi_provider.py
```

---

## 📦 Technology Stack

### Core Dependencies
- **Python**: 3.10+ (for Union types, match/case)
- **httpx**: Async HTTP client
- **geopandas**: Spatial data handling
- **shapely**: Geometry operations
- **pyproj**: CRS transformations
- **pydantic**: Data validation (Recipe models)
- **typer**: CLI framework
- **rich**: Beautiful terminal output

### Development Tools
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **mypy**: Static type checking
- **ruff**: Fast Python linter
- **black**: Code formatting

### Optional Extensions
- **OWSLib**: WMS/WFS client (if needed)
- **rasterio**: Raster processing
- **Pillow**: Image handling (WMTS)

---

## 🎯 Development Phases

### **Phase 1: Foundation (Week 1)** ✅ Current
**Goal**: Project skeleton + core architecture

**Tasks:**
- [x] Create project structure
- [ ] Write PLAN.md
- [ ] Set up pyproject.toml (Poetry)
- [ ] Create .gitignore
- [ ] Define Recipe schema (Pydantic models)
- [ ] Define Protocol abstract base class
- [ ] Define Provider abstract base class
- [ ] Basic CLI skeleton (typer)
- [ ] Unit test framework setup

**Deliverable**: `giskit 0.1.0-dev` - Importable package with structure

---

### **Phase 2: Recipe System (Week 2)**
**Goal**: Recipe parser + validator working

**Tasks:**
- [ ] Implement Recipe model (Pydantic)
- [ ] JSON Schema for recipe validation
- [ ] Recipe loader (from file/dict)
- [ ] Location parser (address/point/bbox)
- [ ] Unit tests for Recipe class
- [ ] CLI: `giskit recipe validate <file>`

**Deliverable**: Recipes can be loaded and validated

---

### **Phase 3: PDOK OGC Features (Week 3)**
**Goal**: First working protocol + provider

**Tasks:**
- [ ] Implement OGCFeaturesProtocol
- [ ] Implement PDOKProvider
- [ ] Geocoding via PDOK Locatieserver
- [ ] Download BGT layers (pand, wegdeel)
- [ ] Write to GeoPackage
- [ ] Integration tests with real PDOK API
- [ ] CLI: `giskit run <recipe>` (basic)

**Deliverable**: Can download PDOK BGT data via recipe

**Example Recipe:**
```json
{
  "location": {"type": "address", "value": "Dam 1, Amsterdam", "radius": 500},
  "datasets": [
    {"provider": "pdok", "service": "bgt", "layers": ["pand"]}
  ],
  "output": {"path": "output.gpkg"}
}
```

---

### **Phase 4: OpenStreetMap (Week 4)**
**Goal**: Second provider (global coverage)

**Tasks:**
- [ ] Implement OverpassProtocol
- [ ] Implement OSMProvider
- [ ] Implement NominatimGeocoder
- [ ] Overpass query builder
- [ ] OSM to GeoDataFrame converter
- [ ] Integration tests
- [ ] Multi-provider recipe example

**Deliverable**: Can download OSM data globally

**Example Recipe:**
```json
{
  "location": {"type": "point", "value": [4.89, 52.37], "radius": 1000},
  "datasets": [
    {"provider": "pdok", "service": "bgt", "layers": ["pand"]},
    {"provider": "osm", "query": "amenity=restaurant"}
  ]
}
```

---

### **Phase 5: WMTS Support (Week 5)**
**Goal**: Raster data support

**Tasks:**
- [ ] Implement WMTSProtocol
- [ ] Tile fetcher + stitcher
- [ ] Raster to GeoPackage (GDAL)
- [ ] PDOK AHN (elevation) integration
- [ ] PDOK Luchtfoto (aerial) integration
- [ ] Resolution calculator
- [ ] Mixed vector/raster recipe

**Deliverable**: Can download raster layers (elevation, aerial)

---

### **Phase 6: Provider Indexer (Week 6)**
**Goal**: Auto-discovery of providers

**Tasks:**
- [ ] GetCapabilities parser (WFS)
- [ ] /collections parser (OGC Features)
- [ ] GetCapabilities parser (WMTS)
- [ ] Provider registry builder
- [ ] Capability cache system
- [ ] CLI: `giskit index scan <url>`
- [ ] CLI: `giskit providers list`

**Deliverable**: Can scan and index new providers automatically

---

### **Phase 7: Polish & Beta (Week 7-8)**
**Goal**: Production-ready beta release

**Tasks:**
- [ ] Complete error handling
- [ ] Progress reporting (rich progress bars)
- [ ] Logging framework
- [ ] Recipe templates (10 examples)
- [ ] Documentation (MkDocs)
- [ ] Performance optimization
- [ ] Memory profiling
- [ ] CLI help text polish
- [ ] Integration test suite (90% coverage)

**Deliverable**: `giskit 0.8.0-beta` - Ready for real-world use

---

## 🔧 Recipe Schema Design

### Minimal Recipe
```json
{
  "location": {
    "type": "address",
    "value": "Dam 1, Amsterdam"
  },
  "datasets": [
    {
      "provider": "pdok",
      "service": "bgt",
      "layers": ["pand"]
    }
  ]
}
```

### Full Recipe (All Options)
```json
{
  "recipe": {
    "version": "1.0",
    "name": "Amsterdam Urban Context",
    "description": "Complete dataset for urban planning analysis",
    "author": "A190",
    "created": "2025-01-22T10:00:00Z",
    "tags": ["urban", "planning", "netherlands"]
  },
  
  "location": {
    "type": "address",
    "value": "Dam 1, Amsterdam, Netherlands",
    "provider": "nominatim",
    "radius": 500,
    "buffer_unit": "meters",
    "fallback": {
      "type": "point",
      "value": [4.89, 52.37],
      "crs": "EPSG:4326"
    }
  },
  
  "output": {
    "format": "geopackage",
    "path": "./output/amsterdam.gpkg",
    "crs": "EPSG:28992",
    "overwrite": true,
    "options": {
      "relative_coordinates": true,
      "center_point": "auto",
      "normalize_elevation": true,
      "metadata": {
        "title": "Amsterdam Dataset",
        "abstract": "Generated by GISKit",
        "keywords": ["urban", "planning"]
      }
    }
  },
  
  "datasets": [
    {
      "name": "buildings",
      "provider": "pdok",
      "service": "bgt",
      "protocol": "ogc_features",
      "layers": ["pand"],
      "options": {
        "grid_size": 250,
        "limit": null,
        "attributes": ["identificatie", "status"],
        "cql_filter": "status = 'in gebruik'"
      },
      "enabled": true,
      "required": true
    },
    {
      "name": "elevation",
      "provider": "pdok",
      "service": "ahn4",
      "protocol": "wmts",
      "layers": ["dsm_5m"],
      "options": {
        "resolution": 5,
        "format": "geotiff",
        "zoom": "auto"
      },
      "enabled": true,
      "required": false
    },
    {
      "name": "osm_poi",
      "provider": "openstreetmap",
      "service": "overpass",
      "protocol": "overpass",
      "query": "[out:json];(node['amenity'](around:{{radius}},{{lat}},{{lon}}););out;",
      "enabled": true,
      "required": false,
      "timeout": 30
    }
  ],
  
  "processing": {
    "steps": [
      {
        "type": "merge_layers",
        "inputs": ["buildings", "roads"],
        "output": "base_map"
      },
      {
        "type": "buffer",
        "input": "buildings",
        "distance": 10,
        "output": "building_buffer"
      }
    ]
  },
  
  "metadata": {
    "license": "CC0-1.0",
    "attribution": "Data from PDOK, OpenStreetMap contributors",
    "generated_by": "GISKit 0.1.0"
  }
}
```

---

## 🌐 Provider Support Roadmap

### Beta Release (Weeks 1-8)
- [x] **PDOK** (Netherlands)
  - OGC Features: BGT, BAG
  - WMTS: AHN, Luchtfoto
  - Geocoding: Locatieserver
  
- [ ] **OpenStreetMap** (Global)
  - Overpass API: POI, buildings, roads
  - Nominatim: Geocoding

### Post-Beta (Future)
- [ ] **Copernicus** (EU) - Satellite imagery
- [ ] **USGS** (USA) - National Map, elevation
- [ ] **Kadaster** (NL) - BRK cadastral data
- [ ] **ANK** (Amsterdam) - Municipal infrastructure
- [ ] **Natural Earth** (Global) - Base maps

---

## 🎓 CLI Command Design

```bash
# Recipe execution
giskit run <recipe.json>                    # Execute recipe
giskit run <recipe.json> --dry-run          # Validate without downloading
giskit run <recipe.json> --output <path>    # Override output path

# Recipe management
giskit recipe validate <recipe.json>        # Validate recipe
giskit recipe create --wizard               # Interactive wizard
giskit recipe create --template urban \
  --location "Amsterdam" \
  --output recipe.json

# Provider exploration
giskit providers list                       # List all providers
giskit providers list --country NL          # Filter by country
giskit providers info pdok                  # Show provider details
giskit providers test pdok --service bgt    # Test connection

# Provider indexing
giskit index scan <url>                     # Scan provider capabilities
giskit index scan <url> --output pdok.json  # Save to file
giskit index update                         # Update all cached providers

# Search
giskit search "buildings" --provider pdok   # Search layers
giskit search "elevation"                   # Search all providers

# Debugging
giskit run <recipe.json> --verbose          # Debug output
giskit run <recipe.json> --log-file log.txt # Save logs
```

---

## 📊 Success Criteria (Beta Release)

### Functional Requirements
- ✅ Can load and validate JSON recipes
- ✅ Can geocode addresses via Nominatim/PDOK
- ✅ Can download PDOK BGT vector data
- ✅ Can download OSM data via Overpass
- ✅ Can download PDOK raster data (AHN/Luchtfoto)
- ✅ Can write multi-layer GeoPackage
- ✅ Supports CRS transformation
- ✅ CLI commands work end-to-end

### Quality Requirements
- **Test Coverage**: >80%
- **Type Coverage**: 100% (mypy strict)
- **Documentation**: Complete API docs + 5 tutorials
- **Performance**: <10s for 1000 vector features
- **Error Handling**: Graceful failures with clear messages

### Example Recipes
- [x] NL Urban Planning (PDOK BGT + BAG3D)
- [ ] NL Environmental (PDOK + CBS + Nature areas)
- [ ] Global OSM POI (OSM Overpass)
- [ ] EU Elevation (Copernicus DEM)
- [ ] Mixed Providers (PDOK + OSM)

---

## 🔐 Authentication Strategy

```json
{
  "datasets": [
    {
      "provider": "pdok",
      "auth": null
    },
    {
      "provider": "ank",
      "auth": {
        "type": "api_key",
        "key_env": "ANK_API_KEY"
      }
    },
    {
      "provider": "custom_wfs",
      "auth": {
        "type": "basic",
        "username_env": "WFS_USER",
        "password_env": "WFS_PASS"
      }
    },
    {
      "provider": "oauth_service",
      "auth": {
        "type": "oauth2",
        "client_id_env": "OAUTH_CLIENT_ID",
        "client_secret_env": "OAUTH_SECRET",
        "token_url": "https://auth.example.com/token"
      }
    }
  ]
}
```

---

## 🧪 Testing Strategy

### Unit Tests (pytest)
- Recipe parsing and validation
- Protocol implementations (mocked HTTP)
- Provider implementations (mocked responses)
- Geocoding logic
- CRS transformations
- GeoPackage writing

### Integration Tests (pytest + real APIs)
- PDOK BGT download (small bbox)
- OSM Overpass query (small area)
- Nominatim geocoding
- Multi-provider recipe
- Error handling (invalid bbox, API down)

### Performance Tests
- 10,000 features download
- Large raster (1km x 1km elevation)
- Memory profiling
- Concurrent downloads

---

## 📝 Development Notes

### Design Decisions
1. **Async by default**: All downloaders use httpx.AsyncClient
2. **Pydantic models**: Type-safe recipe validation
3. **Protocol abstraction**: Easy to add new protocols
4. **Provider registry**: JSON files, not hardcoded
5. **GeoPackage output**: Single-file, QGIS-compatible

### Known Challenges
- **CRS complexity**: Different providers use different CRS
- **Rate limiting**: Need to handle API quotas
- **Large rasters**: Memory management for WMTS
- **Auth diversity**: OAuth, API keys, Basic auth
- **Error recovery**: Partial downloads, retry logic

### Future Features (Post-Beta)
- [ ] Web UI for recipe builder
- [ ] Incremental updates (only new/changed data)
- [ ] Data fusion (conflate overlapping sources)
- [ ] Caching layer (local tile cache)
- [ ] Cloud storage output (S3, Azure)
- [ ] Streaming mode (process on-the-fly)
- [ ] Plugin system (custom protocols/providers)

---

## 🚀 Next Steps

### This Week
1. ✅ Create project structure
2. ✅ Write PLAN.md
3. [ ] Set up pyproject.toml
4. [ ] Create README.md
5. [ ] Implement Recipe Pydantic models
6. [ ] Write recipe JSON schema
7. [ ] Create first unit tests

### Next Week
1. [ ] Implement Protocol base class
2. [ ] Implement OGCFeaturesProtocol
3. [ ] Implement PDOKProvider
4. [ ] Basic CLI (giskit run)
5. [ ] First integration test (PDOK BGT)
6. [ ] Example recipe: Amsterdam BGT

---

## 📚 References

### Standards
- [OGC API - Features](https://ogcapi.ogc.org/features/)
- [WFS 2.0 Specification](https://www.ogc.org/standards/wfs)
- [WMTS 1.0 Specification](https://www.ogc.org/standards/wmts)
- [GeoPackage Encoding Standard](https://www.geopackage.org/)

### APIs
- [PDOK API Documentation](https://api.pdok.nl/)
- [OSM Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)

### Python Libraries
- [httpx](https://www.python-httpx.org/)
- [geopandas](https://geopandas.org/)
- [pydantic](https://docs.pydantic.dev/)
- [typer](https://typer.tiangolo.com/)

---

## 👥 Contributors

- **A190** - Initial concept and development

---

## 📄 License

To be determined (likely MIT for permissive open source)

---

**Last Updated**: 2025-01-22  
**Next Review**: After Phase 1 completion
