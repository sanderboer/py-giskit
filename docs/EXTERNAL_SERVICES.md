# External Services Integration Guide

## Overview

This document covers data sources and services that are **NOT** included in PDOK (Publieke Dienstverlening Op de Kaart) but are valuable for real estate feasibility analysis in the Netherlands.

For PDOK services (BGT, BAG, BRK, AHN, etc.), see [PDOK_SERVICES_OVERVIEW.md](PDOK_SERVICES_OVERVIEW.md).

---

## Why These Services Are External

PDOK focuses on **base registrations** (basisregistraties) and government geographic data. The following services are maintained by specialized organizations or require different licensing:

1. **OV Haltes** - Real-time transit data (NDOV, commercial)
2. **Scholen** - Education facilities (DUO, different ministry)
3. **Energielabels** - Energy performance certificates (RVO, commercial API)
4. **Monumenten** - Heritage sites (RCE, partially in PDOK but limited)
5. **Klimaatatlas** - Climate adaptation data (separate portal)
6. **Bestemmingsplannen** - Zoning plans (IMRO, complex WFS)

---

## 1. OV Haltes (Public Transport Stops)

### Data Source
- **Provider:** NDOV (Nationale Databank Openbaar Vervoer)
- **Alternative:** 9292 API, NS API
- **Format:** GTFS, REST API
- **Update frequency:** Real-time / Daily

### Why Not in PDOK?
- Commercial data from transport operators
- Real-time components require different infrastructure
- Managed by transport ministry (IenW), not BZK

### API Details

**NDOV Loket (Open Data):**
```python
# GTFS Static feed (daily updates)
GTFS_URL = "http://gtfs.ovapi.nl/nl/gtfs-nl.zip"

# Real-time positions
REALTIME_API = "http://v0.ovapi.nl/stopareacode/{code}"
```

**Implementation Example:**
```python
import requests
import geopandas as gpd
from shapely.geometry import Point

def get_transit_stops_near_project(bbox, buffer_m=500):
    """
    Get OV stops within buffer of project location

    Args:
        bbox: (minx, miny, maxx, maxy) in RD coordinates
        buffer_m: Buffer distance in meters

    Returns:
        GeoDataFrame with stop locations and metadata
    """

    # NDOV GTFS feed (download and cache)
    stops_url = "http://gtfs.ovapi.nl/nl/stops.txt"

    # Parse GTFS stops.txt
    stops = pd.read_csv(stops_url)

    # Convert lat/lon to RD (EPSG:28992)
    geometry = [Point(lon, lat) for lon, lat in zip(stops.stop_lon, stops.stop_lat)]
    gdf = gpd.GeoDataFrame(stops, geometry=geometry, crs="EPSG:4326")
    gdf = gdf.to_crs("EPSG:28992")

    # Filter to bbox + buffer
    minx, miny, maxx, maxy = bbox
    mask = (
        (gdf.geometry.x >= minx - buffer_m) &
        (gdf.geometry.x <= maxx + buffer_m) &
        (gdf.geometry.y >= miny - buffer_m) &
        (gdf.geometry.y <= maxy + buffer_m)
    )

    return gdf[mask][['stop_name', 'stop_code', 'geometry']]
```

### Integration Effort
- **Complexity:** Low-Medium
- **Time estimate:** 2-3 days
- **Caching strategy:** Daily GTFS update, cache stop locations
- **Dependencies:** `gtfs-kit` or manual CSV parsing

---

## 2. Scholen (Schools)

### Data Source
- **Provider:** DUO (Dienst Uitvoering Onderwijs)
- **Format:** CSV, Open Data Portal
- **Update frequency:** Annually (October)

### Why Not in PDOK?
- Managed by education ministry (OCW)
- Not a base registration (basisregistratie)
- No official WFS service

### API Details

**DUO Open Data:**
```python
# Primary/Secondary schools addresses
SCHOOLS_URL = "https://duo.nl/open_onderwijsdata/databestanden/po/adressen/adressen-po-3.csv"

# Metadata (school types, student counts)
METADATA_URL = "https://duo.nl/open_onderwijsdata/databestanden/po/leerlingen/leerlingen-po-3.csv"
```

**Implementation Example:**
```python
def get_schools_near_project(bbox, school_types=['bo', 'so'], buffer_m=1000):
    """
    Get schools within buffer of project location

    Args:
        bbox: (minx, miny, maxx, maxy) in RD coordinates
        school_types: ['bo'] = primary, ['vo'] = secondary, ['so'] = special
        buffer_m: Buffer distance in meters

    Returns:
        GeoDataFrame with school locations and student counts
    """

    import pandas as pd
    import geopandas as gpd
    from geopy.geocoders import Nominatim  # For address geocoding

    # Download CSV (cache annually)
    schools = pd.read_csv(SCHOOLS_URL, sep=';', encoding='latin1')

    # Geocode addresses to RD coordinates (cache results!)
    # DUO provides addresses but NOT coordinates
    # Use BAG or geocoding service

    # Option 1: Match with BAG addresses (recommended)
    # Option 2: Geocode using geopy (slow, rate-limited)

    # Filter school types
    schools = schools[schools['denominatie'].isin(school_types)]

    # ... geocoding logic here ...

    return gdf_schools
```

### Integration Effort
- **Complexity:** Medium (requires geocoding)
- **Time estimate:** 2 days
- **Caching strategy:** Annual CSV update, geocode once and cache coordinates
- **Challenge:** DUO provides addresses NOT coordinates → need BAG matching

**Recommended approach:**
1. Download DUO CSV annually
2. Match addresses with BAG addresses (using GISKit BAG provider)
3. Cache geocoded results in PostGIS
4. Serve via WFS endpoint

---

## 3. Energielabels (Energy Performance Certificates)

### Data Source
- **Provider:** RVO (Rijksdienst voor Ondernemend Nederland)
- **API:** EP-Online API (requires registration)
- **Update frequency:** Real-time (labels valid 10 years)

### Why Not in PDOK?
- Commercial/privacy considerations
- Managed by economic affairs ministry (EZK)
- REST API model (not OGC standards)

### API Details

**EP-Online API v2:**
```python
# API endpoint (requires API key)
API_BASE = "https://public.ep-online.nl/api/v2"

# Endpoints
LABEL_BY_ADDRESS = f"{API_BASE}/PandEnergielabel/Adres"
LABEL_BY_BAG = f"{API_BASE}/PandEnergielabel/Pandidentificatie"
```

**Implementation Example:**
```python
def get_energy_labels_for_area(bag_ids, api_key):
    """
    Get energy labels for BAG panden

    Args:
        bag_ids: List of BAG pand identificaties
        api_key: EP-Online API key

    Returns:
        DataFrame with energy labels and registration dates
    """

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    results = []
    for bag_id in bag_ids:
        response = requests.get(
            f"{LABEL_BY_BAG}/{bag_id}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            results.append({
                'bag_id': bag_id,
                'energielabel': data['Energieklasse'],
                'opnamedatum': data['Opnamedatum'],
                'energieindex': data['Energieindex']
            })

    return pd.DataFrame(results)
```

### Integration Effort
- **Complexity:** Low-Medium
- **Time estimate:** 3-5 days
- **Cost:** API access is paid (check RVO pricing)
- **Rate limits:** Check EP-Online API documentation

**Use cases:**
- Neighborhood energy efficiency analysis
- Existing building stock quality
- Renovation potential scoring

---

## 4. Monumenten (Heritage Sites)

### Data Source
- **Provider:** RCE (Rijksdienst voor het Cultureel Erfgoed)
- **PDOK status:** Partially available via WFS, but limited metadata
- **Full API:** Monumentenregister API

### Why Separate Documentation?

While PDOK offers a basic `cultuurhistorie` service, the **full monumentenregister** has:
- Detailed descriptions and history
- Photos and documentation
- Heritage value assessments
- Protection status details

### API Details

**RCE Open Data:**
```python
# PDOK WFS (basic geometries)
PDOK_WFS = "https://service.pdok.nl/rce/cultuurhistorie/wfs/v1_0"

# Full monument register (richer data)
RCE_API = "https://monumentenregister.cultureelerfgoed.nl/monumenten.json"
```

**Implementation Example:**
```python
def get_monuments_impact_analysis(project_bbox, buffer_m=100):
    """
    Analyze heritage sites near project

    Args:
        project_bbox: Project bounding box in RD
        buffer_m: Protection zone buffer

    Returns:
        GeoDataFrame with monument details and impact zones
    """

    from giskit.providers import PDOKProvider

    pdok = PDOKProvider()

    # Get monuments from PDOK WFS
    monuments = pdok.get_wfs_features(
        service='cultuurhistorie',
        typename='rijksmonumenten',
        bbox=project_bbox
    )

    # Enrich with RCE API data
    for idx, row in monuments.iterrows():
        monument_id = row['monumentnummer']

        # Fetch full details from RCE
        response = requests.get(
            f"{RCE_API}",
            params={'monumentnummer': monument_id}
        )

        # Add description, photos, etc.
        # ...

    return monuments
```

### Integration Effort
- **Complexity:** Low (basic) / Medium (full enrichment)
- **Time estimate:** 1-2 days
- **Value add:** Cultural heritage impact assessments for building permits

---

## 5. Klimaatatlas (Climate Adaptation)

### Data Source
- **Provider:** Klimaateffectatlas (various government agencies)
- **Format:** WMS layers
- **Themes:** Heat stress, flooding, drought

### Why Not in PDOK?
- Separate climate-focused portal
- Different governance structure
- Thematic maps (not base data)

### API Details

**WMS Services:**
```python
# Heat stress (hittestress)
HEATSTRESS_WMS = "https://geodata.nationaalgeoregister.nl/klimaateffectatlas/wms"

# Flood risk (overstromingsrisico)
FLOOD_WMS = "https://klimaateffectatlas.nl/api/geoserver/wms"
```

**Implementation Example:**
```python
def add_climate_overlay_to_viewer(project_bbox, climate_layer='heatstress'):
    """
    Add climate adaptation WMS layer to 3D viewer

    Args:
        project_bbox: Project area in RD coordinates
        climate_layer: 'heatstress' | 'flood' | 'drought'

    Returns:
        WMS layer configuration for frontend
    """

    layer_mapping = {
        'heatstress': {
            'url': HEATSTRESS_WMS,
            'layers': 'klimaateffectatlas:hittestress_2050',
            'format': 'image/png',
            'transparent': True
        },
        'flood': {
            'url': FLOOD_WMS,
            'layers': 'overstromingsrisico',
            'format': 'image/png',
            'transparent': True
        }
    }

    config = layer_mapping[climate_layer]

    # Generate WMS GetMap URL for bounding box
    wms_url = f"{config['url']}?SERVICE=WMS&VERSION=1.3.0" \
              f"&REQUEST=GetMap&LAYERS={config['layers']}" \
              f"&BBOX={','.join(map(str, project_bbox))}" \
              f"&WIDTH=512&HEIGHT=512&CRS=EPSG:28992" \
              f"&FORMAT={config['format']}&TRANSPARENT=true"

    return {
        'type': 'wms_overlay',
        'url': wms_url,
        'opacity': 0.6,
        'legend_url': f"{config['url']}?REQUEST=GetLegendGraphic&LAYER={config['layers']}"
    }
```

### Integration Effort
- **Complexity:** Low (WMS overlay)
- **Time estimate:** 1-2 days
- **Value:** Climate-aware design for municipalities

---

## 6. Bestemmingsplannen (Zoning Plans)

### Data Source
- **Provider:** Ruimtelijkeplannen.nl (IMRO standard)
- **Format:** WFS (GML), complex XML rules
- **Standard:** IMRO2012

### Why Complex?

Bestemmingsplannen are technically available via WFS, but:
1. **Complex structure:** Multi-level geometries and rules
2. **Legal text parsing:** Building regulations in separate PDF/XML
3. **Versioning:** Multiple plan versions, superseded plans
4. **IMRO standard:** Specialized XML schema

### API Details

**Ruimtelijkeplannen WFS:**
```python
IMRO_WFS = "https://services.rce.geovoorziening.nl/landschapsatlas/wfs"

# Alternative: Direct PDOK access
PDOK_IMRO = "https://service.pdok.nl/rvo/bestemmingsplannen/wfs/v1_0"
```

**Implementation Example:**
```python
def get_zoning_plan_for_location(point_rd):
    """
    Get applicable zoning plan (bestemmingsplan) for location

    Args:
        point_rd: (x, y) in RD coordinates

    Returns:
        Dict with zoning rules and restrictions

    Warning:
        This is simplified - real implementation needs:
        - Plan version resolution (which plan is active?)
        - Rule extraction from complex XML
        - Legal text parsing
    """

    from owslib.wfs import WebFeatureService

    wfs = WebFeatureService(PDOK_IMRO, version='2.0.0')

    # Query for bestemmingsplangebied
    response = wfs.getfeature(
        typename='bestemmingsplangebied',
        bbox=(point_rd[0]-10, point_rd[1]-10, point_rd[0]+10, point_rd[1]+10),
        srsname='EPSG:28992'
    )

    # Parse GML response (complex!)
    # Extract plan identification
    # Fetch detailed rules from separate service

    # This requires specialized IMRO parser library
    # Recommended: Use existing tools like RuimtelijkeplannenExtractor

    return {
        'plan_naam': '...',
        'bestemming': '...',  # e.g., "Wonen - 1"
        'max_bouwhoogte': '...',
        'max_bebouwingspercentage': '...',
        # ... many more fields
    }
```

### Integration Effort
- **Complexity:** HIGH
- **Time estimate:** 2-3 weeks
- **Challenges:**
  - IMRO XML parsing (complex schema)
  - Legal rule extraction (NL-IMRO-0363 standard)
  - Plan versioning and superseding
  - PDF text extraction for detailed rules

**Recommended Approach:**
1. **Phase 1:** Show plan boundaries only (WFS polygons) - **1 week**
2. **Phase 2:** Extract basic attributes (max height, use class) - **+1 week**
3. **Phase 3:** Full rule parsing with legal text - **+2 weeks**

**External libraries to consider:**
- `geoalchemy2` for complex geometry handling
- `lxml` for IMRO XML parsing
- Specialized IMRO parsers (check GitHub)

---

## Integration Priorities

### Quick Wins (< 1 week)
1. **Klimaatatlas WMS** - Simple overlay, high value for municipalities
2. **Monumenten (basic)** - Already in PDOK, just add to viewer
3. **OV Haltes (cached)** - GTFS download + daily cache

### Medium Effort (1-2 weeks)
4. **Scholen** - Geocoding + BAG matching required
5. **Energielabels** - API integration + rate limiting

### Complex (2-3 weeks)
6. **Bestemmingsplannen (full)** - IMRO parsing, legal rules

---

## GISKit Extension Roadmap

### Proposed Structure

```python
# giskit/providers/external.py

class ExternalDataProvider:
    """Provider for non-PDOK government data sources"""

    def get_transit_stops(self, bbox, buffer_m=500):
        """NDOV GTFS integration"""
        pass

    def get_schools(self, bbox, school_types=['bo']):
        """DUO school data with BAG geocoding"""
        pass

    def get_energy_labels(self, bag_ids):
        """EP-Online API integration"""
        pass

    def get_climate_overlay(self, bbox, layer_type):
        """Klimaatatlas WMS layers"""
        pass

    def get_heritage_sites(self, bbox, include_metadata=False):
        """RCE monumentenregister"""
        pass

    def get_zoning_plan(self, point):
        """IMRO bestemmingsplan (basic)"""
        pass
```

### Configuration

```yaml
# giskit/config/services/external.yml

external:
  ndov:
    gtfs_url: "http://gtfs.ovapi.nl/nl/gtfs-nl.zip"
    cache_duration: 86400  # 24 hours

  duo:
    schools_url: "https://duo.nl/open_onderwijsdata/..."
    update_frequency: "annual"
    geocoding_service: "bag"  # Use BAG for address matching

  ep_online:
    api_base: "https://public.ep-online.nl/api/v2"
    api_key: "${EP_ONLINE_API_KEY}"  # Environment variable
    rate_limit: 100  # requests per minute

  klimaateffectatlas:
    wms_base: "https://geodata.nationaalgeoregister.nl/klimaateffectatlas/wms"
    layers:
      - hittestress_2050
      - overstromingsrisico
      - droogte
```

---

## Use Cases Per Data Source

| Data Source | Woningbouwcorporaties | Gemeenten | Projectontwikkelaars |
|-------------|----------------------|-----------|---------------------|
| **OV Haltes** | ⭐⭐⭐ Bereikbaarheid sociale huur | ⭐⭐ Mobiliteitsbeleid | ⭐⭐⭐ Locatie attractiviteit |
| **Scholen** | ⭐⭐⭐ Gezinswoningen locatie | ⭐⭐⭐ Onderwijsvoorzieningen | ⭐⭐ Doelgroep families |
| **Energielabels** | ⭐⭐⭐ Bestaande voorraad | ⭐⭐ Verduurzamingsbeleid | ⭐ Marktanalyse |
| **Monumenten** | ⭐ Renovatie beperkingen | ⭐⭐⭐ Erfgoed bescherming | ⭐⭐ Bouwkosten impact |
| **Klimaatatlas** | ⭐⭐ Klimaatadaptatie | ⭐⭐⭐ Hittestress beleid | ⭐⭐ Future-proof design |
| **Bestemmingsplan** | ⭐⭐ Programma validatie | ⭐⭐⭐ Juridische toets | ⭐⭐⭐ Haalbaarheid check |

---

## Next Steps

1. **Prioritize based on client needs** - Survey target users for must-have vs. nice-to-have
2. **Start with quick wins** - Klimaatatlas WMS overlay (2 days implementation)
3. **Build caching infrastructure** - PostGIS + Redis for geocoded results
4. **API key management** - Secure storage for EP-Online credentials
5. **Extend GISKit** - Add `ExternalDataProvider` class to core library

---

## Questions?

For PDOK services implementation, see [PDOK_SERVICES_OVERVIEW.md](PDOK_SERVICES_OVERVIEW.md).

For GISKit core functionality, see [README.md](README.md).

**Contact:** Open an issue in the GISKit repository for external service integration requests.
