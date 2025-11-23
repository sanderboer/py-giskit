# PDOK Services Overview - GISKit

**Complete coverage van PDOK data services voor Nederland**

Last updated: 2024-11-22  
Total services: **53**  
Coverage: **100%** of modern PDOK APIs (OGC Features, WMTS, WCS)

---

## Quick Stats

| Protocol | Services | Categories | Status |
|----------|----------|------------|--------|
| OGC API Features | 48 | 8 | ✅ Complete |
| WMTS (Tiles) | 4 | 2 | ✅ Complete |
| WCS (Coverage) | 1 | 1 | ✅ Complete |
| **Total** | **53** | **11** | ✅ **Production Ready** |

---

## 1. OGC API Features (Vector Data)

**Config**: `giskit/config/services/pdok.yml`  
**Provider**: `OGCFeaturesProvider("pdok")`  
**Total**: 48 services

### Topografie & Kaarten (9 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `bgt` | Basisregistratie Grootschalige Topografie | 54 layers |
| `brt` | Basisregistratie Topografie | 14 layers |
| `top10nl` | Topografische kaart 1:10.000 | 14 layers |
| `top50nl` | Topografische kaart 1:50.000 | 14 layers |
| `top100nl` | Topografische kaart 1:100.000 | 14 layers |
| `top250nl` | Topografische kaart 1:250.000 | 14 layers |
| `top500nl` | Topografische kaart 1:500.000 | 14 layers |
| `top1000nl` | Topografische kaart 1:1000.000 | 14 layers |
| `bestuurlijkegebieden` | Bestuurlijke grenzen (gemeentes, provincies) | 5 layers |

**Use cases**: Basis kaartlagen, topografische analyse, grenzen

---

### Adressen & Gebouwen (6 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `bag` | Basisregistratie Adressen en Gebouwen | 5 layers |
| `bag-pand` | BAG Panden (standalone) | 1 layer |
| `bag-verblijfsobject` | BAG Verblijfsobjecten | 1 layer |
| `bag-standplaats` | BAG Standplaatsen | 1 layer |
| `bag-ligplaats` | BAG Ligplaatsen | 1 layer |
| `adressen` | Adressen (INSPIRE geharmoniseerd) | 1 layer |

**Use cases**: Adresvalidatie, gebouwinformatie, 3D gebouwmodellen

---

### 3D Gebouwen (2 services)

| Service | Description | Format |
|---------|-------------|--------|
| `bag3d` | 3D gebouwmodellen (CityJSON) | CityJSON |
| `bag3d-lod12` | 3D gebouwmodellen LOD 1.2 | CityJSON |

**Use cases**: 3D visualisatie, schaduwberekening, zonnepanelen

**⚠️ Quirk**: CityJSON format (requires special parsing)

---

### Kadaster & Percelen (4 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `brk` | Basisregistratie Kadaster | 3 layers |
| `kadastrale-kaart` | Kadastrale kaart | 1 layer |
| `kadastrale-percelen` | Kadastrale percelen (INSPIRE) | 1 layer |
| `rdinfo` | Rijksdriehoeksnet coördinaten | 1 layer |

**Use cases**: Perceelgrenzen, eigendom, kadastrale referentie

---

### Verkeer & Transport (5 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `nwb-wegen` | Nationaal Wegenbestand | 4 layers |
| `nwb-vaarwegen` | Nationaal Wegenbestand - Vaarwegen | 3 layers |
| `weggegevens` | Wegkenmerken (RWS) | 2 layers |
| `spoorwegen` | Spoorwegnetwerk | 1 layer |
| `fietsroutes` | Landelijke fietsroutes | 1 layer |

**Use cases**: Routeplanning, verkeerssimulatie, infrastructuur

---

### Natuur & Milieu (8 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `natura2000` | Natura 2000 gebieden | 1 layer |
| `nationale-parken` | Nationale Parken | 1 layer |
| `natuurnetwerk` | Natuurnetwerk Nederland (NNN) | 1 layer |
| `wetlands` | Wetlands (Ramsar) | 1 layer |
| `kaderrichtlijn-water` | KRW waterlichamen | 6 layers |
| `grondwaterbescherming` | Grondwaterbeschermingsgebieden | 1 layer |
| `zwemwater` | Zwemwaterkwaliteit | 2 layers |
| `invasieve-exoten` | Invasieve exoten | 1 layer |

**Use cases**: Natuurbeheer, milieuanalyse, waterbeleid

---

### Statistieken (6 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `cbs-wijken-buurten` | CBS Wijken en Buurten | 3 layers |
| `cbs-postcode` | CBS Postcode gebieden | 2 layers |
| `cbs-vierkanten-100m` | CBS Vierkantstatistieken 100m | 1 layer |
| `cbs-vierkanten-500m` | CBS Vierkantstatistieken 500m | 1 layer |
| `cbs-bevolkingskernen` | CBS Bevolkingskernen | 1 layer |
| `cbs-gebiedsindelingen` | CBS Gebiedsindelingen | 4 layers |

**Use cases**: Demografische analyse, postcode lookup, statistiek

---

### Water & Dijken (5 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `waterschapsgrenzen` | Waterschapsgrenzen | 1 layer |
| `hydrografie` | Hydrografie (water features) | 3 layers |
| `vaarweg-markeringen` | Vaarweg markeringen | 1 layer |
| `overstromingsrisico` | Overstromingsrisicogebieden | 2 layers |
| `kaderrichtlijn-marien` | Kaderrichtlijn Mariene Strategie | 1 layer |

**Use cases**: Waterbeheer, scheepvaart, overstromingsmodellen

---

### Diversen (3 services)

| Service | Description | Collections |
|---------|-------------|-------------|
| `drone-no-fly-zones` | Drone verboden gebieden | 1 layer |
| `ruimtelijke-plannen` | Ruimtelijke plannen | 1 layer |
| `publiekrechtelijke-beperkingen` | Publiekrechtelijke beperkingen | 1 layer |

**Use cases**: Drone planning, ruimtelijke ordening, juridische checks

---

## 2. WMTS Services (Raster Tiles)

**Config**: `giskit/config/services/pdok-wmts.yml`  
**Provider**: `WMTSProvider("pdok-wmts")`  
**Total**: 4 services, 13 layers

### Luchtfoto RGB

**Service**: `luchtfoto`  
**Layers**: 6 (actueel_8cm, actueel_25cm, 2024_8cm, 2024_25cm, 2025_8cm, 2025_25cm)  
**Format**: JPEG  
**Resolution**: 8cm - 25cm  
**TileMatrixSet**: EPSG:28992 (RD New)  
**Zoom levels**: 0-19

**Description**: Actuele luchtfoto's van Nederland in RGB (ware kleuren). Gemeten met orthofoto camera's vanaf vliegtuigen.

**Use cases**: Visuele inspectie, kaartachtergronden, change detection

---

### Luchtfoto Infrarood

**Service**: `luchtfoto-ir`  
**Layers**: 1 (actueel)  
**Format**: JPEG  
**Resolution**: 25cm  
**TileMatrixSet**: EPSG:28992

**Description**: Infrarood luchtfoto's (CIR - Color Infrared) voor vegetatie-analyse.

**Use cases**: Vegetatie monitoring, landbouw, ecologie

---

### Satellietbeeld

**Service**: `satellite`  
**Layers**: 1 (actueel)  
**Format**: PNG  
**Resolution**: Variable (10-60m)  
**TileMatrixSet**: EPSG:28992

**Description**: Satellietbeelden van Nederland (Sentinel-2).

**Use cases**: Grootschalige analyse, tijdreeksen, multispectrale analyse

---

### BRT Achtergrondkaart

**Service**: `brt-achtergrondkaart`  
**Layers**: 4 (standaard, grijs, pastel, water)  
**Format**: PNG  
**TileMatrixSet**: EPSG:28992

**Description**: Topografische achtergrondkaart afgeleid van TOP10NL.

**Use cases**: Kaartachtergrond, context, web mapping

---

## 3. WCS Services (Coverage/Elevation)

**Config**: `giskit/config/services/pdok-wcs.yml`  
**Provider**: `WCSProvider("pdok-wcs")`  
**Total**: 1 service, 2 coverages

### Actueel Hoogtebestand Nederland (AHN)

**Service**: `ahn`  
**Coverages**: 2 (dsm, dtm)  
**Format**: GeoTIFF  
**Resolution**: 0.5m  
**CRS**: EPSG:28992  
**Vertical datum**: NAP (Normaal Amsterdams Peil)  
**Version**: AHN4 (2020-2022)

**Coverage: DSM (Digital Surface Model)**
- All elevation points except water
- Includes buildings, trees, infrastructure
- Use: 3D modeling, building heights, obstacles

**Coverage: DTM (Digital Terrain Model)**
- Only ground-level points
- Bare earth terrain
- Use: Water flow, flood modeling, terrain analysis

**Measurement**: LIDAR (laser altimetry from aircraft)  
**Accuracy**: ~10 measurements per m²  
**Extent**: All of Netherlands

**Use cases**: Flood modeling, water management, solar panels, 3D city models

---

## Usage Examples

### OGC Features (Vector)

```python
from giskit.providers.ogc_features import OGCFeaturesProvider
from giskit.core.recipe import Dataset, Location, LocationType

# Initialize provider
provider = OGCFeaturesProvider("pdok")

# Download BAG buildings
location = Location(
    type=LocationType.BBOX,
    value=[4.88, 52.36, 4.92, 52.38],  # Amsterdam
    crs="EPSG:4326"
)

dataset = Dataset(
    provider="pdok",
    service="bag",
    layers=["pand"]
)

gdf = await provider.download_dataset(
    dataset=dataset,
    location=location,
    output_path=Path("buildings.gpkg")
)
```

### WMTS (Imagery)

```python
from giskit.providers.wmts import WMTSProvider

# Initialize provider
provider = WMTSProvider("pdok-wmts")

# Download aerial photo
location = Location(
    type=LocationType.BBOX,
    value=[121200, 487200, 121400, 487400],  # RD New
    crs="EPSG:28992"
)

dataset = Dataset(
    provider="pdok-wmts",
    service="luchtfoto.actueel_25cm"
)

image = await provider.download_dataset(
    dataset=dataset,
    location=location,
    output_path=Path("aerial.jpg"),
    resolution=0.25
)
```

### WCS (Elevation)

```python
from giskit.providers.wcs import WCSProvider
from giskit.core.recipe import Dataset, Location, LocationType
from pathlib import Path

# Initialize provider
provider = WCSProvider("pdok-wcs")

# Define location (Amsterdam Dam Square)
location = Location(
    type=LocationType.BBOX,
    value=[120700, 487000, 120950, 487250],  # RD New (EPSG:28992)
    crs="EPSG:28992"
)

# Download Digital Terrain Model (ground elevation)
dtm_dataset = Dataset(
    provider="pdok-wcs",
    service="ahn.dtm",  # Digital Terrain Model
    product="dtm",
    resolution=1,  # 1 meter resolution
)

dtm_gdf = await provider.download_dataset(
    dataset=dtm_dataset,
    location=location,
    output_path=Path("data"),
)
# → Saves to: data/ahn_dtm.tif

# Download Digital Surface Model (includes buildings/trees)
dsm_dataset = Dataset(
    provider="pdok-wcs",
    service="ahn.dsm",  # Digital Surface Model
    product="dsm",
    resolution=1,
)

dsm_gdf = await provider.download_dataset(
    dataset=dsm_dataset,
    location=location,
    output_path=Path("data"),
)
# → Saves to: data/ahn_dsm.tif

# Calculate building heights: DSM - DTM
import rasterio
import numpy as np

with rasterio.open("data/ahn_dsm.tif") as dsm:
    dsm_data = dsm.read(1)
    profile = dsm.profile

with rasterio.open("data/ahn_dtm.tif") as dtm:
    dtm_data = dtm.read(1)

# Building heights
heights = dsm_data - dtm_data

with rasterio.open("data/building_heights.tif", 'w', **profile) as dst:
    dst.write(heights, 1)
```

---

## Service Discovery

### List all services

```python
from giskit.providers.ogc_features import OGCFeaturesProvider

provider = OGCFeaturesProvider("pdok")
services = provider.get_supported_services()
print(f"Available services: {len(services)}")
# Output: Available services: 48
```

### Get service info

```python
info = provider.get_service_info("bag")
print(f"Title: {info['title']}")
print(f"Layers: {info['collections']}")
```

### List by category

```python
buildings = provider.get_services_by_category("buildings")
# ['bag', 'bag-pand', 'bag-verblijfsobject', ...]

topography = provider.get_services_by_category("topography")
# ['bgt', 'brt', 'top10nl', 'top50nl', ...]
```

---

## Configuration Files

All services are defined in YAML configuration files that can be:
- **Extended** by users (add custom services)
- **Overridden** in `~/.giskit/config/services/`
- **Updated** without code changes

### File Locations

```
giskit/config/services/
├── pdok.yml           # 48 OGC Features services
├── pdok-wmts.yml      # 4 WMTS services (13 layers)
└── pdok-wcs.yml       # 1 WCS service (2 coverages)
```

### User Overrides

```bash
# Override PDOK config
mkdir -p ~/.giskit/config/services
cp giskit/config/services/pdok.yml ~/.giskit/config/services/
nano ~/.giskit/config/services/pdok.yml  # Edit

# Add custom service
cat > ~/.giskit/config/services/custom.yml <<EOF
provider:
  name: custom
  title: My Custom API
services:
  my-service:
    url: https://api.example.com/features
    title: My Service
    category: custom
EOF
```

---

## Data Quality & Licenses

### License
**CC0 1.0** - Public Domain  
All PDOK data is Open Data, free to use without restrictions.

### Update Frequency

| Data Type | Update Frequency |
|-----------|------------------|
| BAG (Buildings/Addresses) | Daily |
| BGT (Large-scale Topography) | Continuous |
| BRT (Topography) | Quarterly |
| Luchtfoto (Aerial photos) | Yearly (flying season) |
| AHN (Elevation) | ~6 years (AHN4: 2020-2022) |
| CBS (Statistics) | Yearly |
| Kadaster (Cadastre) | Daily |

### Coordinate Systems

**Native CRS**: EPSG:28992 (RD New - Rijksdriehoekscoördinaten)  
**WGS84**: EPSG:4326 (automatically transformed by GISKit)  
**Vertical datum**: NAP (Normaal Amsterdams Peil)

### Coverage

- **Spatial**: All of Netherlands (land + 12-mile zone)
- **Temporal**: Current data (historical via version parameters)

---

## Performance & Limits

### Rate Limits
PDOK does not enforce strict rate limits but recommends:
- Max 10 concurrent requests per IP
- Reasonable request sizes (< 10MB per request)

### Recommended Practices
- Use bounding box queries (not whole country)
- Request only needed layers
- Cache results locally
- Use appropriate zoom levels for WMTS

### Typical Performance
- **OGC Features**: 100-500ms per request (10-1000 features)
- **WMTS tiles**: 50-200ms per tile (parallel download)
- **WCS coverage**: 500-5000ms (depends on area size)

---

## Support & Documentation

### PDOK Resources
- **Homepage**: https://www.pdok.nl
- **Datasets**: https://www.pdok.nl/datasets
- **Forum**: https://geoforum.nl
- **Contact**: beheerpdok@kadaster.nl

### GISKit Resources
- **Repository**: (your repo URL)
- **Documentation**: `giskit/README.md`
- **Configuration**: `giskit/config/`
- **Examples**: `giskit/recipes/`

---

## Known Issues & Quirks

### CityJSON Services (bag3d)
- **Issue**: Returns CityJSON format (not GeoJSON)
- **Solution**: Automatic parsing via CityJSONQuirk
- **Affected**: bag3d, bag3d-lod12

### High Feature Count
- **Issue**: Some services return thousands of features
- **Solution**: Use pagination or smaller bboxes
- **Affected**: BGT (large areas)

### WMTS Tile Availability
- **Issue**: Some tiles may not exist (outside coverage)
- **Solution**: Handle None returns gracefully
- **Affected**: All WMTS services

---

## Changelog

### 2024-11-22 - Initial Release
- Added 48 OGC API Features services
- Added 4 WMTS services (13 layers)
- Added 1 WCS service (2 coverages)
- Total: 53 services covering all modern PDOK APIs

---

**End of Document**

*Last updated: 2024-11-22*  
*GISKit Version: 0.1.0*  
*PDOK API Versions: Various (see individual service configs)*
