# PDOK Services Catalog

Complete catalog of all 40+ PDOK (Publieke Dienstverlening Op de Kaart) services available through giskit.

**Total Services**: 40+
**Categories**: 6 (Base Registers, Topography, Statistics, Infrastructure, Environment, Administrative)
**Coverage**: Netherlands
**License**: CC0 1.0 (public domain)
**Homepage**: https://www.pdok.nl

---

## Service Categories

### 1. Base Registers (Basisregistraties)

Core Dutch government registers with authoritative spatial data.

| Service Key | Title | Description |
|------------|-------|-------------|
| `bgt` | Basisregistratie Grootschalige Topografie | Large-scale topography base register with 46 detailed object layers |
| `bag` | Basisregistratie Adressen en Gebouwen | National address and building register |
| `brk` | Basisregistratie Kadaster | Cadastral map with parcel boundaries |
| `bag3d` | 3D BAG | 3D building models with LOD support (hosted at api.3dbag.nl) |

**Example layers**:
- BGT: `pand`, `wegdeel`, `waterdeel`, `begroeidterreindeel`, `onbegroeidterreindeel`
- BAG: `pand`, `verblijfsobject`, `ligplaats`, `standplaats`, `woonplaats`

---

### 2. Topography (Topografie)

Maps, 3D models, and topographic data at various scales.

| Service Key | Title | Description |
|------------|-------|-------------|
| `3d-basisvoorziening` | 3D Basisvoorziening | 3D base map with height information from BGT, BAG, and AHN4 |
| `3d-geluid` | 3D Geluid | 3D environment model for noise calculations |
| `brt-achtergrondkaart` | BRT Achtergrondkaart | Background map derived from TOP10NL |
| `top10nl` | BRT TOP10NL | Topographic map at 1:10,000 scale |
| `brt-bodemgebruik` | Bodemgebruik (INSPIRE) | Land cover classification (INSPIRE harmonized) |
| `brt-geografische-namen` | Geografische Namen (INSPIRE) | Geographic place names (INSPIRE harmonized) |
| `brt-hydrografie` | Hydrografie (INSPIRE) | Water features and hydrography (INSPIRE harmonized) |
| `brt-vervoersnetwerken` | Vervoersnetwerken (INSPIRE) | Transport networks (INSPIRE harmonized) |
| `brt-zeegebieden` | Zeegebieden (INSPIRE) | Sea areas (INSPIRE harmonized) |

---

### 3. CBS Statistics (Statistieken)

Demographic and statistical data from Statistics Netherlands (CBS).

| Service Key | Title | Description |
|------------|-------|-------------|
| `cbs-wijken-buurten-2024` | CBS Wijken en Buurten 2024 | Neighborhoods and districts with demographics (2024) |
| `cbs-wijken-buurten-2023` | CBS Wijken en Buurten 2023 | Neighborhoods and districts with demographics (2023) |
| `cbs-wijken-buurten-2022` | CBS Wijken en Buurten 2022 | Neighborhoods and districts with demographics (2022) |
| `cbs-gebiedsindelingen` | CBS Gebiedsindelingen 2016-heden | Current administrative area divisions |
| `cbs-gebiedsindelingen-historisch` | CBS Gebiedsindelingen 1995-2015 | Historical administrative area divisions |
| `cbs-vierkant-100m` | CBS Vierkantstatistieken 100m | 100m grid statistics |
| `cbs-vierkant-500m` | CBS Vierkantstatistieken 500m | 500m grid statistics |
| `cbs-postcode4` | CBS Postcode4 statistieken | 4-digit postcode area statistics |
| `cbs-postcode6` | CBS Postcode6 statistieken | 6-digit postcode area statistics |
| `cbs-bevolkingskernen-2021` | CBS Bevolkingskernen 2021 | Population centers 2021 |
| `cbs-bevolkingskernen-2011` | CBS Bevolkingskernen 2011 | Population centers 2011 |
| `cbs-bodemgebruik-2017` | CBS Bestand Bodemgebruik 2017 | Land use statistics 2017 |
| `cbs-bodemgebruik-2015` | CBS Bestand Bodemgebruik 2015 | Land use statistics 2015 |
| `cbs-bodemgebruik-2010` | CBS Bestand Bodemgebruik 2010 | Land use statistics 2010 |
| `cbs-landuse` | CBS Existing Land Use (INSPIRE) | Land use (INSPIRE harmonized) |
| `cbs-population-distribution` | CBS Population Distribution (INSPIRE) | Population distribution (INSPIRE harmonized) |
| `cbs-human-health` | CBS Human Health Statistics (INSPIRE) | Health statistics (INSPIRE harmonized) |

---

### 4. Infrastructure (Infrastructuur)

Roads, railways, waterways, and transport networks.

| Service Key | Title | Description |
|------------|-------|-------------|
| `nwb-wegen` | Nationaal Wegenbestand - Wegen | National road network |
| `nwb-vaarwegen` | Nationaal Wegenbestand - Vaarwegen | National waterway network |
| `spoorwegen` | Spoorwegen | Railway network (ProRail) |
| `weggegevens` | Weggegevens | Road data and attributes |
| `vaarwegmarkeringen` | Vaarwegmarkeringen Nederland | Waterway markings and navigation aids |

---

### 5. Environment (Milieu & Natuur)

Nature conservation, protected areas, agriculture, and sustainability.

| Service Key | Title | Description |
|------------|-------|-------------|
| `natura2000` | Natura 2000 | EU protected nature areas |
| `natura2000-inspire` | Natura 2000 (INSPIRE) | EU protected nature areas (INSPIRE harmonized) |
| `nationale-parken` | Nationale Parken | Dutch national parks |
| `nationale-parken-inspire` | Nationale Parken (INSPIRE) | Dutch national parks (INSPIRE harmonized) |
| `gewaspercelen` | Basisregistratie Gewaspercelen (BRP) | Agricultural crop parcels |
| `habitatrichtlijn-typen` | Habitatrichtlijn - Habitattypen | Habitat types distribution (Habitat Directive) |
| `habitatrichtlijn-soorten` | Habitatrichtlijn - Soorten | Species distribution (Habitat Directive) |
| `vogelrichtlijn-soorten` | Vogelrichtlijn - Soorten | Bird species distribution (Birds Directive) |
| `wetlands` | Wetlands | Wetland areas |
| `wetlands-inspire` | Wetlands (INSPIRE) | Wetland areas (INSPIRE harmonized) |

---

### 6. Administrative & Other

Administrative boundaries, cultural heritage, and miscellaneous datasets.

| Service Key | Title | Description |
|------------|-------|-------------|
| `bestuurlijkegebieden` | Bestuurlijke Gebieden | Administrative boundaries (municipalities, provinces, water boards) |
| `cultureel-erfgoed` | Beschermde Gebieden - Cultuurhistorie | Cultural heritage protected areas (INSPIRE harmonized) |
| `drone-nofly` | Drone No-Fly Zones | Restricted airspace for drones |

---

## Usage Examples

### Example 1: Download BGT Data

```python
from giskit.providers import get_provider

# Get PDOK provider
provider = get_provider("pdok")

# List all services
services = provider.get_supported_services()
print(f"Available services: {len(services)}")

# Get services by category
stats_services = provider.get_services_by_category("statistics")
print(f"CBS Statistics services: {stats_services}")

# Get detailed service info
info = provider.get_service_info("bgt")
print(f"BGT: {info['title']}")
print(f"Description: {info['description']}")
```

### Example 2: Use Recipe for Multi-Service Download

```json
{
  "name": "Curieweg Complete Dataset",
  "location": {
    "type": "address",
    "value": "Curieweg 7a, Spijkenisse, Netherlands",
    "radius": 1000
  },
  "datasets": [
    {
      "provider": "pdok",
      "service": "bgt",
      "layers": ["pand", "wegdeel", "waterdeel"]
    },
    {
      "provider": "pdok",
      "service": "cbs-wijken-buurten-2024",
      "layers": ["buurten", "wijken"]
    },
    {
      "provider": "pdok",
      "service": "natura2000",
      "layers": ["natura2000"]
    }
  ]
}
```

### Example 3: Query Service Metadata

```python
# List all categories
categories = provider.list_categories()
# Returns: ['administrative', 'aviation', 'base_registers', 'culture',
#           'environment', 'infrastructure', 'statistics', 'topography']

# Get service info
bag_info = provider.get_service_info("bag")
print(f"URL: {bag_info['url']}")
print(f"Keywords: {bag_info['keywords']}")
```

---

## Service Discovery

All services support:
- **OGC Features API** protocol
- **Bounding box queries** (WGS84 and RD New)
- **Pagination** for large datasets
- **CRS transformation** (output in any CRS)
- **GeoPackage export**

### Programmatic Service Discovery

```python
from giskit.providers.pdok import PDOK_SERVICES

# Browse all services
for service_key, service_config in PDOK_SERVICES.items():
    if isinstance(service_config, dict):
        print(f"{service_key}: {service_config['title']}")
        print(f"  Category: {service_config['category']}")
        print(f"  URL: {service_config['url']}")
```

---

## Special Cases

### BAG3D (External Host)

The `bag3d` service is hosted at `api.3dbag.nl` (not `api.pdok.nl`) and requires special handling:

```json
{
  "provider": "pdok",
  "service": "bag3d",
  "layers": ["pand"],
  "lod": "2.2"
}
```

**Note**: BAG3D returns CityJSON features with 3D geometry, while other services return GeoJSON.

---

## INSPIRE Harmonized Services

Services with `-inspire` suffix are harmonized according to the INSPIRE directive (EU spatial data infrastructure). These services use standardized schemas for cross-border interoperability.

**Examples**:
- `natura2000-inspire`
- `nationale-parken-inspire`
- `wetlands-inspire`
- `cbs-landuse`
- `cbs-population-distribution`

---

## Recipe Examples

See `giskit/recipes/` for complete examples:

1. **`curieweg_bgt_complete.json`** - All 46 BGT layers
2. **`curieweg_cbs_statistics.json`** - CBS demographic data
3. **`curieweg_infrastructure.json`** - Roads, waterways, railways
4. **`curieweg_environment.json`** - Nature and protected areas
5. **`curieweg_topography.json`** - Topographic maps and 3D data
6. **`curieweg_multi_service.json`** - Combined multi-service dataset

---

## API Endpoints

All services use the OGC Features API (OAF) specification:

**Base URL Pattern**: `https://api.pdok.nl/{organization}/{service}/ogc/{version}/`

**Examples**:
- BGT: `https://api.pdok.nl/lv/bgt/ogc/v1_0/`
- BAG: `https://api.pdok.nl/lv/bag/ogc/v1_0/`
- CBS: `https://api.pdok.nl/cbs/wijken-en-buurten-2024/ogc/v1/`
- NWB: `https://api.pdok.nl/rws/nationaal-wegenbestand-wegen/ogc/v1/`

---

## Attribution

When using PDOK data, please provide appropriate attribution:

```
© Kadaster / PDOK
```

For CBS data:
```
© Centraal Bureau voor de Statistiek (CBS)
```

For specific services, check the service metadata for detailed attribution requirements.

---

## API Quirks & Known Issues

### PDOK OGC Features API Quirks

All PDOK services require specific URL handling:

1. **Trailing Slash Required**: Base URLs must end with `/` to prevent urljoin() issues
2. **Format Parameter Required**: All requests must include `?f=json` parameter
3. **Auto-handled by giskit**: These quirks are automatically handled by the quirks system

### CityJSON Format (3D Services)

**⚠️ CRITICAL**: Services using CityJSON format have important quirks related to coordinate transformation!

**Affected Services**:
- `bag3d` - 3D BAG building models
- `3d-basisvoorziening` - 3D base map (may use CityJSON)
- `3d-geluid` - 3D noise environment (may use CityJSON)

**CityJSON Format Quirks**:

1. **Per-Page Transform (CRITICAL)** ⚠️
   - Each pagination page has its **own** `transform` (scale/translate)
   - Transform values vary **per page**, not globally
   - Applying wrong transform causes coordinate errors!
   - **Solution**: Tag each feature with its page's transform before processing

2. **Integer Vertex Compression**
   - Vertices stored as integers, not real coordinates
   - Formula: `real_coord = vertex[i] * scale[i] + translate[i]`
   - Must extract transform from `metadata.transform` or `transform`
   - Transform has `scale` [x, y, z] and `translate` [x, y, z] arrays

3. **CityJSON Structure**
   - Format is CityJSON 2.0, not standard GeoJSON
   - Has `CityObjects` structure instead of simple features
   - Geometry stored in LOD hierarchy (Building → BuildingPart → geometry → LOD)
   - Two geometry sources:
     1. GeoJSON `geometry` field (preferred if available)
     2. CityJSON `vertices` + `boundaries` (fallback)

**Example Transform Bug** (from production):

```python
# ❌ WRONG: Using same transform for all features
transform = first_page_data["metadata"]["transform"]
for page in all_pages:
    for feature in page["features"]:
        coords = apply_transform(feature["vertices"], transform)  # BUG!

# ✅ CORRECT: Track transform per page
for page in all_pages:
    page_transform = page["metadata"]["transform"]  # Extract per page
    for feature in page["features"]:
        feature["_page_transform"] = page_transform  # Tag with source
        coords = apply_transform(feature["vertices"], page_transform)
```

**References**:
- CityJSON 2.0 Spec: https://www.cityjson.org/specs/2.0.0/#transform-object
- BAG3D API Docs: https://api.3dbag.nl/api.html
- Sitedb Reference Implementation: `Sitedb/sitedb/core/bag3d_downloader.py:87-100`

**Note**: As of November 2025, BAG3D API may return standard GeoJSON instead of CityJSON. The quirks system documents the historical CityJSON format for reference and other CityJSON sources.

---

## Further Reading

- **PDOK Homepage**: https://www.pdok.nl
- **PDOK API Documentation**: https://api.pdok.nl
- **OGC Features API Spec**: https://ogcapi.ogc.org/features/
- **INSPIRE Directive**: https://inspire.ec.europa.eu/
- **CityJSON Specification**: https://www.cityjson.org/

---

**Last Updated**: November 22, 2025
**giskit Version**: 0.1.0
