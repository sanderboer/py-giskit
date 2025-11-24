# Klimaatadaptatie Data Sources voor GISKit

Dit document beschrijft welke klimaatadaptatie databronnen toegevoegd kunnen worden aan GISKit.

## Prioriteit: HOOG (Direct implementeerbaar)

### 1. Klimaateffectatlas (KNMI)

**Bron**: https://www.klimaateffectatlas.nl/
**API**: OGC WMS/WFS (mogelijk)
**Complexity**: LOW-MEDIUM
**Data**:
- Hittekaarten (Urban Heat Island)
- Droogtekaarten
- Wateroverlastkaarten
- Klimaatscenario's (2050, 2085)

**Implementatie**:
```yaml
# config/providers/knmi.yml
provider:
  name: "KNMI"
  title: "KNMI - Klimaateffectatlas"
  homepage: "https://www.klimaateffectatlas.nl/"
  coverage: "Netherlands"

services:
  hitte:
    title: "Hittekaarten"
    url: "https://klimaateffectatlas.nl/api/..."
    protocol: "wms"  # of ogc-features
    category: "climate"
    keywords: [hitte, warmte, uhi, klimaat]
```

**Geschiktheid**: ⭐⭐⭐⭐⭐
- Direct relevant voor klimaatadaptatie
- Nationale dekking
- Wetenschappelijk onderbouwd (KNMI)

---

### 2. Klimaatatlas (Atlas Leefomgeving)

**Bron**: https://www.atlasleefomgeving.nl/klimaat
**API**: REST API + WMS
**Complexity**: LOW
**Data**:
- Stedelijk hitte-eiland effect
- Kwetsbare gebieden (ouderen, kinderen)
- Groenvoorziening
- Verhardingskaarten

**Implementatie**: Vergelijkbaar met KNMI, mogelijk via WMS protocol

**Geschiktheid**: ⭐⭐⭐⭐⭐
- Interactieve kaarten al beschikbaar
- API waarschijnlijk aanwezig
- Direct bruikbaar voor gemeenten

---

### 3. Waterinfo.nl (Rijkswaterstaat)

**Bron**: https://waterinfo.rws.nl/
**API**: REST API + OGC services
**Complexity**: MEDIUM
**Data**:
- Actuele waterstanden
- Grondwaterstanden
- Neerslagdata
- Stroomsnelheden
- Historische data

**Implementatie**:
```yaml
# config/providers/waterinfo.yml
provider:
  name: "Waterinfo"
  title: "Waterinfo - Rijkswaterstaat"
  api_base: "https://waterinfo.rws.nl/api/"

services:
  waterstanden:
    title: "Actuele Waterstanden"
    url: "https://waterinfo.rws.nl/api/..."
    protocol: "rest-api"  # Custom protocol needed
    category: "water"
    realtime: true
```

**Geschiktheid**: ⭐⭐⭐⭐
- Real-time data
- Belangrijk voor wateroverlast
- Vereist custom REST API protocol

---

### 4. Bodemdata.nl (BRO - Basisregistratie Ondergrond)

**Bron**: https://www.broloket.nl/
**API**: OGC WFS + REST API
**Complexity**: MEDIUM
**Data**:
- Grondwaterstanden
- Bodemsamenstelling (doorlatendheid)
- Grondboringen
- Geotechnische eigenschappen

**Implementatie**:
```yaml
# config/providers/bro.yml
provider:
  name: "BRO"
  title: "Basisregistratie Ondergrond"
  homepage: "https://www.broloket.nl/"

services:
  grondwaterstanden:
    title: "Grondwatermonitoring"
    url: "https://publiek.broservices.nl/gm/gmw/v1"
    protocol: "ogc-features"
    category: "subsurface"
```

**Geschiktheid**: ⭐⭐⭐⭐
- Wetenschappelijk belangrijk
- Infiltratiecapaciteit bepalen
- Al OGC standaard (makkelijk!)

---

## Prioriteit: MEDIUM (Vereist extra werk)

### 5. Stresstestkaarten (Gemeenten)

**Bron**: Gemeentelijke open data portals
**API**: Varieert per gemeente
**Complexity**: HIGH (per gemeente anders)
**Data**:
- Hittekaarten per gemeente
- Wateroverlastkaarten
- Droogtekaarten

**Voorbeelden**:
- Amsterdam: https://data.amsterdam.nl/
- Rotterdam: https://rotterdamopendata.nl/
- Utrecht: https://data.utrecht.nl/

**Implementatie**: Multi-provider aanpak nodig

**Geschiktheid**: ⭐⭐⭐
- Zeer gedetailleerd
- Gemeente-specifiek
- Fragmentatie is probleem

---

### 6. Natuurwaarden (NDFF)

**Bron**: https://www.ndff.nl/
**API**: NDFF Verspreidingsatlas API
**Complexity**: MEDIUM-HIGH
**Data**:
- Flora verspreidingsdata
- Fauna verspreidingsdata
- Biodiversiteit indicatoren

**Geschiktheid**: ⭐⭐⭐
- Belangrijk voor groene klimaatadaptatie
- API vereist waarschijnlijk authenticatie
- Privacygevoelige data (exacte locaties beschermd)

---

### 7. Urbis (Kadaster) - Stedelijke Data

**Bron**: https://www.kadaster.nl/urbis
**API**: Mogelijk via PDOK
**Complexity**: MEDIUM
**Data**:
- 3D stadsmodellen
- Gebouwfuncties
- Energielabels (mogelijk)

**Geschiktheid**: ⭐⭐⭐
- Aanvullend op BAG3D
- Mogelijke overlap met bestaande data

---

## Prioriteit: LOW (Nice-to-have)

### 8. Satellietdata (Copernicus/ESA)

**Bron**: https://scihub.copernicus.eu/
**API**: Sentinel Hub API
**Complexity**: HIGH
**Data**:
- Sentinel-2 multispectrale beelden
- NDVI (vegetatie-index)
- Temperatuur kaarten
- Veranderingsdetectie

**Implementatie**: Vereist nieuwe "sentinel" protocol

**Geschiktheid**: ⭐⭐
- Zeer krachtig maar complex
- Grote data volumes
- Vereist processing

---

### 9. Rioolstelsels (Gemeenten)

**Bron**: Gemeentelijke data
**API**: Varieert (vaak GeoJSON dumps)
**Complexity**: HIGH
**Data**:
- Rioolbuizen
- Putten
- Capaciteit

**Geschiktheid**: ⭐⭐
- Belangrijk voor wateroverlast
- Zeer gefragmenteerd
- Privacy/security gevoelig

---

## Implementatie Aanbevelingen

### Fase 1: Quick Wins (1-2 weken)
1. ✅ **BRO (Basisregistratie Ondergrond)** - Al OGC Features!
2. ✅ **Waterinfo.nl** - REST API, custom protocol nodig
3. ⚠️ **Klimaateffectatlas** - Check API beschikbaarheid

### Fase 2: Medium Term (1 maand)
4. **Atlas Leefomgeving** klimaatdata
5. **NDFF** natuurdata (als API beschikbaar)

### Fase 3: Long Term (3+ maanden)
6. Gemeentelijke stresstests (multi-provider)
7. Sentinel satellietdata (complex)

---

## Code Voorbeelden

### Voorbeeld 1: BRO Grondwater toevoegen

```yaml
# config/providers/bro.yml
provider:
  name: "BRO"
  title: "Basisregistratie Ondergrond"
  description: "Subsurface data including groundwater and soil"
  homepage: "https://www.broloket.nl/"
  coverage: "Netherlands"
  attribution: "BRO / TNO"

services:
  grondwaterstanden:
    title: "Grondwatermonitoring"
    description: |
      Grondwaterstanden van alle monitoringsputten in Nederland.
      Belangrijk voor infiltratiecapaciteit en wateroverlast.
    url: "https://publiek.broservices.nl/gm/gmw/v1"
    protocol: "ogc-features"
    category: "subsurface"
    keywords:
      - grondwater
      - groundwater
      - bro
      - infiltratie
      - klimaatadaptatie
    format: "geojson"
```

**Gebruik**:
```python
from giskit.providers.base import get_provider

# Auto-discovered from config!
bro = get_provider("bro")
services = bro.get_supported_services()
# ['grondwaterstanden']
```

### Voorbeeld 2: Waterinfo REST API

Vereist nieuw protocol:

```python
# giskit/protocols/waterinfo.py
class WaterinfoProtocol(Protocol):
    """REST API protocol for Waterinfo.nl"""

    async def get_waterstanden(self, location_ids: list[str]):
        """Get current water levels for locations."""
        url = f"{self.base_url}/v1/waterstanden"
        params = {"locations": ",".join(location_ids)}

        response = await self.client.get(url, params=params)
        data = response.json()

        # Convert to GeoDataFrame
        return self._to_geodataframe(data)
```

### Voorbeeld 3: Recipe voor Klimaatadaptatie

```json
{
  "name": "Klimaatadaptatie Analyse Utrecht",
  "description": "Alle relevante klimaatdata voor Utrecht Centraal",
  "location": {
    "type": "point",
    "value": [5.1108, 52.0894],
    "radius": 1000,
    "crs": "EPSG:4326"
  },
  "datasets": [
    {
      "service": "ahn",
      "provider": "pdok",
      "product": "dtm",
      "resolution": 0.5
    },
    {
      "service": "bgt",
      "provider": "pdok",
      "layers": ["wegdeel", "waterdeel", "begroeidterreindeel"]
    },
    {
      "service": "grondwaterstanden",
      "provider": "bro"
    },
    {
      "service": "hitte",
      "provider": "knmi",
      "scenario": "2050-WH"
    }
  ]
}
```

---

## Benodigde Tools

### 1. REST API Protocol
Voor Waterinfo.nl en andere REST APIs:
```python
# giskit/protocols/rest_api.py
class RestAPIProtocol(Protocol):
    """Generic REST API protocol with JSON/GeoJSON output"""
```

### 2. WMS Protocol (voor kaartlagen)
Voor Klimaateffectatlas en Atlas Leefomgeving:
```python
# giskit/protocols/wms.py
class WMSProtocol(Protocol):
    """WMS (Web Map Service) for raster data"""
```

### 3. Time Series Support
Voor Waterinfo realtime data:
```python
# giskit/core/timeseries.py
class TimeSeriesData:
    """Handle temporal data (water levels, temperature)"""
```

---

## Prioriteit Samenvatting

| Databron | Prioriteit | Complexiteit | Impact | Status |
|----------|-----------|--------------|--------|--------|
| **BRO Grondwater** | 🔴 HOOG | LOW | Hoog | ⏳ Te implementeren |
| **Waterinfo.nl** | 🔴 HOOG | MEDIUM | Hoog | ⏳ Nieuw protocol nodig |
| **Klimaateffectatlas** | 🔴 HOOG | MEDIUM | Zeer hoog | ⏳ API check nodig |
| **Atlas Leefomgeving** | 🟡 MEDIUM | LOW-MEDIUM | Hoog | ⏳ WMS mogelijk |
| **NDFF Natuur** | 🟡 MEDIUM | MEDIUM | Medium | ⏳ API authenticatie |
| **Gemeentelijke stress** | 🟢 LOW | HIGH | Hoog | ⏳ Fragmentatie |
| **Sentinel satelliet** | 🟢 LOW | VERY HIGH | Medium | ⏳ Complex |

---

## Volgende Stappen

1. **Check API beschikbaarheid**:
   - BRO: https://publiek.broservices.nl/ ✅ (OGC Features)
   - Waterinfo: https://waterinfo.rws.nl/api/ ⚠️ (REST, check docs)
   - KNMI Klimaateffectatlas: ⚠️ (API check nodig)

2. **Implementeer BRO** (1-2 dagen):
   - Config file maken
   - Testen met bestaand OGC Features protocol
   - Documentatie

3. **Implementeer REST API protocol** (2-3 dagen):
   - Generic RestAPIProtocol class
   - Waterinfo.nl als eerste use case
   - Tests

4. **Documentatie** (1 dag):
   - Klimaatadaptatie use cases
   - Recipe voorbeelden
   - Tutorial

**Total effort**: ~1-2 weken voor basis klimaatadaptatie support
