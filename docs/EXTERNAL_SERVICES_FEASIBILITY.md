# External Services Integration - Feasibility Analysis

**Date:** November 24, 2025
**Project:** GISKit - Python toolkit for spatial data
**Scope:** Integration feasibility for 5 external Dutch data services

---

## Executive Summary

This document analyzes the feasibility of integrating 5 external data services into GISKit:

| Service | Status | Complexity | API Access | Recommendation |
|---------|--------|------------|------------|----------------|
| **1. OV Haltes (NDOV)** | ✅ Active | 🟢 Low | Free, no key | **HIGH PRIORITY** - Quick win |
| **2. Scholen (DUO)** | ✅ Active | 🟡 Medium | Free, no key | **MEDIUM PRIORITY** - Needs geocoding |
| **3. Energielabels (EP-Online)** | ✅ Active | 🟡 Medium | Free, API key required | **MEDIUM PRIORITY** - Business value |
| **4. Monumenten (RCE)** | ✅ Active | 🟢 Low | Free, no key | **HIGH PRIORITY** - Quick win |
| **5. Klimaatatlas** | ✅ Active | 🟢 Low | Free, no key | **HIGH PRIORITY** - Quick win |

**Overall Assessment:** All 5 services are **feasible and recommended** for integration. Three are "quick wins" (1-3 days each), two require moderate effort (3-5 days).

**Total Implementation Time:** 2-3 weeks for all 5 services

---

## 1. OV Haltes (Public Transport Stops)

### Service Status: ✅ ACTIVE

**Provider:** NDOV Loket (Nationale Databank Openbaar Vervoer)
**Data Source:** http://gtfs.ovapi.nl/nl/
**Last Verified:** November 24, 2025

### API Details

- **GTFS Static Feed:** `http://gtfs.ovapi.nl/nl/gtfs-nl.zip` (258MB, daily updates)
- **GTFS-RT Feeds:** Protocol Buffer format, real-time updates
  - Trip updates: `http://gtfs.ovapi.nl/nl/tripUpdates.pb`
  - Vehicle positions: `http://gtfs.ovapi.nl/nl/vehiclePositions.pb`
  - Alerts: `http://gtfs.ovapi.nl/nl/alerts.pb`

### Access Requirements

✅ **Completely Free & Open**
- No API key required
- CC0 license (public domain)
- No registration needed
- Fair use policy (identify in User-Agent, use caching)

### Data Coverage

- **Complete Netherlands coverage** including:
  - NS (national railways)
  - All regional bus/train operators (Arriva, Connexxion, EBS, Qbuzz)
  - Urban transport (GVB Amsterdam, HTM The Hague, RET Rotterdam)
  - Ferries and international connections

- **stops.txt** contains ~60,000 stops with lat/lon coordinates
- Updated daily at 03:00 UTC

### Integration Complexity: 🟢 LOW

**Effort Estimate:** 2-3 days

**Implementation Approach:**

1. **Static Data Integration:**
   - Download GTFS feed daily (cache with HTTP headers)
   - Parse `stops.txt` for stop locations
   - Convert WGS84 coordinates to RD (EPSG:28992)
   - Store in PostGIS or return as GeoDataFrame

2. **Architecture Fit:**
   - Create new provider: `giskit.providers.ndov.NDOVProvider`
   - Use existing HTTP client infrastructure
   - Leverage GeoDataFrame/spatial query patterns

3. **Code Example:**
```python
# giskit/providers/ndov.py
class NDOVProvider(Provider):
    """NDOV public transport data provider."""

    def __init__(self, name: str = "ndov", **kwargs):
        super().__init__(name, **kwargs)
        self.gtfs_url = "http://gtfs.ovapi.nl/nl/gtfs-nl.zip"

    async def get_stops(self, bbox: tuple, crs: str = "EPSG:28992") -> gpd.GeoDataFrame:
        """Get transit stops within bounding box."""
        # Download + parse GTFS
        # Filter to bbox
        # Return GeoDataFrame
```

### Use Cases

- **Woningbouwcorporaties:** ⭐⭐⭐ Bereikbaarheid sociale huur (accessibility analysis)
- **Projectontwikkelaars:** ⭐⭐⭐ Locatie attractiviteit (location scoring)
- **Gemeenten:** ⭐⭐ Mobiliteitsbeleid (transport planning)

### Recommendation: ✅ **HIGH PRIORITY - IMPLEMENT**

**Rationale:**
- Easy integration (standard GTFS format)
- High business value for site feasibility
- No API barriers or costs
- Daily updates ensure freshness
- Fits GISKit architecture perfectly

---

## 2. Scholen (Schools)

### Service Status: ✅ ACTIVE

**Provider:** DUO (Dienst Uitvoering Onderwijs)
**Data Portal:** https://onderwijsdata.duo.nl/
**Last Verified:** November 24, 2025

### API Details

**Primary Schools CSV:**
```
https://onderwijsdata.duo.nl/dataset/786f12ea-6224-42fd-ab72-de4d7d879535/
  resource/9801fdea-01bc-43cc-8e4e-3e03a2bbbbf8/download/instellingenbo.csv
```

**Secondary Schools CSV:**
```
https://onderwijsdata.duo.nl/dataset/c8e6ffdd-cc2b-44ee-880f-0ff03f72e868/
  resource/0ef14f5e-89bf-4e92-b28e-8d323b7b8dbc/download/instellingenvo.csv
```

### Data Format

- **Format:** CSV (UTF-8, comma-separated)
- **Size:** ~6,000 primary schools, ~1,500 secondary schools
- **Update Frequency:** Monthly
- **Fields:** 29 columns including:
  - INSTELLINGSCODE (BRIN code - unique ID)
  - INSTELLINGSNAAM (school name)
  - STRAATNAAM, HUISNUMMER-TOEVOEGING, POSTCODE, PLAATSNAAM
  - DENOMINATIE (school type: public, Catholic, Protestant, etc.)
  - GEMEENTENUMMER, GEMEENTENAAM
  - Regional codes (COROP, RPA, etc.)

### Access Requirements

✅ **Completely Free & Open**
- No API key required
- CC-BY license
- No registration needed
- CKAN API available: `https://onderwijsdata.duo.nl/api/3/`

### Critical Issue: ❌ NO COORDINATES

**Data contains only addresses, NOT lat/lon coordinates**

### Integration Complexity: 🟡 MEDIUM

**Effort Estimate:** 3-4 days

**Challenge:** Geocoding addresses to coordinates

**Implementation Options:**

**Option 1: PDOK Locatieserver (Recommended)**
- Use PDOK free geocoding API
- `https://api.pdok.nl/bzk/locatieserver/search/v3_1/`
- Excellent for Dutch addresses
- No API key required

**Option 2: BAG Matching**
- Match addresses with BAG (Basisregistratie Adressen en Gebouwen)
- Use POSTCODE + HUISNUMMER for precise matching
- More complex but most accurate

**Option 3: Pre-geocode and Cache**
- Geocode all schools once per month
- Store in PostGIS database
- Serve via GISKit provider

### Architecture Approach

```python
# giskit/providers/duo.py
class DUOProvider(Provider):
    """DUO education facilities provider."""

    async def get_schools(
        self,
        bbox: tuple,
        school_types: list[str] = ["bo", "vo"],  # primary, secondary
        crs: str = "EPSG:28992"
    ) -> gpd.GeoDataFrame:
        """Get schools within bounding box."""

        # Download CSV
        schools_df = await self._download_schools(school_types)

        # Geocode addresses (cached)
        gdf = await self._geocode_schools(schools_df)

        # Filter to bbox
        return gdf[gdf.within(bbox)]

    async def _geocode_schools(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        """Geocode school addresses using PDOK Locatieserver."""
        # Use POSTCODE + HUISNUMMER for precise geocoding
        # Cache results for 1 month
```

### Use Cases

- **Woningbouwcorporaties:** ⭐⭐⭐ Gezinswoningen locatie (family housing)
- **Gemeenten:** ⭐⭐⭐ Onderwijsvoorzieningen planning
- **Projectontwikkelaars:** ⭐⭐ Doelgroep families (target demographics)

### Recommendation: ✅ **MEDIUM PRIORITY - IMPLEMENT**

**Rationale:**
- High business value for residential projects
- Geocoding adds complexity but is solvable
- Monthly updates are acceptable
- PDOK Locatieserver provides free geocoding
- Can be pre-geocoded and cached

**Implementation Strategy:**
1. **Phase 1:** Download CSV + PDOK geocoding (2 days)
2. **Phase 2:** Add caching/PostGIS storage (1 day)
3. **Phase 3:** Integrate with GISKit provider pattern (1 day)

---

## 3. Energielabels (Energy Performance Certificates)

### Service Status: ✅ ACTIVE

**Provider:** RVO (Rijksdienst voor Ondernemend Nederland)
**Portal:** https://www.ep-online.nl/
**API Portal:** https://apikey.ep-online.nl/
**Last Verified:** November 24, 2025

### API Details

**Openbare Data (Public Data Files):**
- **Totaalbestand:** Monthly snapshot of all valid energy labels
- **Mutatiebestanden:** Daily mutation files
- **Formats:** XML, CSV, XLSX
- **Size:** ~300MB (November 2025 total file)

**Access Method:**
- Download via web interface: https://www.ep-online.nl/PublicData
- Requires **API key** (free, but registration needed)

### Data Content

Energy labels for 8+ million buildings:
- **Pand identificatie** (BAG building ID)
- **Energieklasse** (A++++ to G)
- **Energieindex** (numerical value)
- **Opnamedatum** (registration date)
- **Geldig tot** (valid until date)
- Building type, postal code, etc.

### Access Requirements

⚠️ **Free but requires API key**

**Registration Process:**
1. Visit https://apikey.ep-online.nl/
2. Fill form: organization name, KvK number, email, organization type
3. Accept terms of use
4. Receive activation link via email (within 24 hours)
5. Click link to get API key
6. API key valid for 1 year (renewable)

**Constraints:**
- No cost (free)
- No rate limits mentioned
- Must identify organization type (makelaardij, gemeente, etc.)
- KvK number required (for Dutch organizations)

### Integration Complexity: 🟡 MEDIUM

**Effort Estimate:** 3-5 days

**Challenges:**
1. **API Key Management:** Need secure storage of API key
2. **Large Files:** 300MB monthly downloads
3. **Data Matching:** Join with BAG panden using pand identificatie
4. **Update Strategy:** Monthly total + daily mutations

### Architecture Approach

```python
# giskit/providers/ep_online.py
class EPOnlineProvider(Provider):
    """RVO EP-Online energy labels provider."""

    def __init__(self, name: str = "ep-online", api_key: str = None, **kwargs):
        super().__init__(name, **kwargs)
        self.api_key = api_key or os.getenv("EP_ONLINE_API_KEY")

    async def get_energy_labels(
        self,
        bag_ids: list[str],  # List of BAG pand IDs
    ) -> pd.DataFrame:
        """Get energy labels for BAG buildings."""

        # Download monthly totaalbestand (cached)
        labels_df = await self._download_labels_file()

        # Filter to requested BAG IDs
        return labels_df[labels_df["pand_identificatie"].isin(bag_ids)]

    async def _download_labels_file(self) -> pd.DataFrame:
        """Download and cache monthly energy labels file."""
        url = "https://www.ep-online.nl/PublicData/Download"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Download CSV (cache for 1 month)
        # Parse and return DataFrame
```

### Use Cases

- **Woningbouwcorporaties:** ⭐⭐⭐ Bestaande voorraad kwaliteit (stock quality)
- **Gemeenten:** ⭐⭐ Verduurzamingsbeleid (sustainability policy)
- **Projectontwikkelaars:** ⭐ Marktanalyse (market analysis)

### Recommendation: ✅ **MEDIUM PRIORITY - IMPLEMENT**

**Rationale:**
- High business value for housing corporations
- Free (but requires registration)
- Good integration with BAG data
- Monthly updates acceptable
- Large files but cacheable

**Requirements for Users:**
- Must obtain API key (one-time registration)
- Store API key in environment variable: `EP_ONLINE_API_KEY`
- Recommended: set up monthly cron job to download updates

**Implementation Strategy:**
1. Add API key configuration to GISKit
2. Implement download + caching (monthly files)
3. Create BAG ID lookup function
4. Document API key registration process

---

## 4. Monumenten (Cultural Heritage)

### Service Status: ✅ ACTIVE

**Provider:** RCE (Rijksdienst voor het Cultureel Erfgoed)
**PDOK Service:** Available
**RCE Portal:** https://monumentenregister.cultureelerfgoed.nl/
**Last Verified:** November 24, 2025

### API Details

**PDOK WFS (Basic Geometry + Metadata):**
```
https://service.pdok.nl/rce/beschermde-gebieden-cultuurhistorie/wfs/v1_0
```

**Dataset Coverage:**
- **Rijksmonumenten:** 63,115+ national monuments
- **Beschermde stads- en dorpsgezichten:** Protected townscapes
- **UNESCO World Heritage sites**

**Data Format:**
- WFS 2.0.0 (standard OGC)
- Also available: WMS, OGC API Features, ATOM

### Access Requirements

✅ **Completely Free & Open**
- No API key required
- No registration
- Standard PDOK access (same as BGT, BAG, etc.)

### Integration Complexity: 🟢 LOW

**Effort Estimate:** 1-2 days

**Rationale:**
- Already fits existing PDOK provider pattern
- Standard WFS protocol
- No special authentication
- Same architecture as existing BGT/BAG integration

### Architecture Approach

**Option 1: Add to Existing PDOK Provider (Recommended)**
```yaml
# giskit/config/services/pdok.yml
services:
  monumenten:
    url: "https://service.pdok.nl/rce/beschermde-gebieden-cultuurhistorie/wfs/v1_0"
    title: "Rijksmonumenten en Beschermde Stads- en Dorpsgezichten"
    category: "culture"
    description: "National monuments and protected townscapes"
    keywords: ["monumenten", "erfgoed", "cultuur", "unesco"]
```

**Option 2: Enrich with RCE Data**
```python
# Future enhancement: fetch detailed metadata from RCE
# using monument numbers as keys
async def enrich_monument_data(monument_number: str) -> dict:
    """Fetch detailed description, photos, history from RCE."""
    # RCE Linked Data platform or web scraping
```

### Use Cases

- **Woningbouwcorporaties:** ⭐ Renovatie beperkingen (renovation constraints)
- **Gemeenten:** ⭐⭐⭐ Erfgoed bescherming (heritage protection)
- **Projectontwikkelaars:** ⭐⭐ Bouwkosten impact (cost analysis)

### Recommendation: ✅ **HIGH PRIORITY - QUICK WIN**

**Rationale:**
- Minimal effort (already have PDOK infrastructure)
- Standard OGC protocol
- Fits existing architecture perfectly
- High value for municipalities
- Can be enriched later with RCE metadata

**Implementation:**
1. Add service config to `pdok.yml` (30 minutes)
2. Test WFS access (30 minutes)
3. Document usage (30 minutes)
4. **Total: ~2 hours**

---

## 5. Klimaatatlas (Climate Adaptation)

### Service Status: ✅ ACTIVE

**Provider:** Ministerie van Infrastructuur en Waterstaat (via Geodan)
**WMS Endpoint:**
```
https://cas.cloud.sogelink.com/public/data/org/gws/YWFMLMWERURF/kea_public/wms
```
**Portal:** https://klimaateffectatlas.nl/
**Last Verified:** November 24, 2025

### API Details

**Service Type:** WMS 1.3.0 + WFS 2.0.0

**Available Layers:** 216+ queryable layers covering:

1. **Hittestress (Heat Stress):**
   - `gevoelstemperatuur_2022` - Heat index 2m resolution
   - `tropischedagen_2050hoog` - Tropical days projection
   - `hitteeiland` - Urban heat island effect

2. **Overstromingsrisico (Flooding):**
   - `overstromingsdiepte_grote_kans` - High probability flood depth
   - `overstromingsdiepte_kleine_kans` - Low probability flood depth
   - Multiple probability scenarios

3. **Droogte (Drought):**
   - `droogtestress_2050hoog` - Drought stress 2050
   - `neerslagtekort_avg_2050hoog` - Precipitation deficit

4. **Wateroverlast (Pluvial Flooding):**
   - `kans_grondwateroverlast_2050hoog` - Groundwater flooding risk
   - `dagen_25mm_2050hoog` - Heavy rain days

### Access Requirements

✅ **Completely Free & Open**
- No API key
- No registration
- CC-BY 4.0 license
- Attribution required: "Klimaateffectatlas, 2025"

### Data Quality

- **Coverage:** Complete Netherlands
- **Resolution:** 2m (heat), 100m (flooding), neighborhood aggregation
- **CRS:** EPSG:28992 (RD), CRS:84 (WGS84)
- **Update Frequency:** Multiple times per year
- **Recent Updates:** Transitioning from KNMI'14 to KNMI'23 climate scenarios

### Integration Complexity: 🟢 LOW

**Effort Estimate:** 2-3 days

**Rationale:**
- Standard WMS/WFS protocols
- Can leverage existing WMTS/WCS provider patterns
- No authentication needed
- RD coordinate system (native GISKit CRS)

### Architecture Approach

```yaml
# giskit/config/services/klimaateffectatlas.yml
provider:
  name: "klimaateffectatlas"
  title: "Klimaateffectatlas"
  country: "NL"
  homepage: "https://klimaateffectatlas.nl"
  license: "CC-BY-4.0"

services:
  hittestress:
    url: "https://cas.cloud.sogelink.com/public/data/org/gws/YWFMLMWERURF/kea_public/wms"
    title: "Hittestress en Hitteeiland"
    category: "climate"
    layers:
      actueel: "gevoelstemperatuur_2022"
      projectie_2050: "tropischedagen_2050hoog"
      hitteeiland: "hitteeiland"

  overstromingsrisico:
    url: "https://cas.cloud.sogelink.com/public/data/org/gws/YWFMLMWERURF/kea_public/wms"
    title: "Overstromingsrisico"
    category: "climate"
    layers:
      hoog: "overstromingsdiepte_grote_kans"
      laag: "overstromingsdiepte_kleine_kans"
```

```python
# giskit/providers/klimaateffectatlas.py
class KlimaatatlasProvider(WMSProvider):
    """Climate adaptation WMS provider."""

    async def get_climate_overlay(
        self,
        bbox: tuple,
        layer_type: str = "heatstress",  # heatstress, flooding, drought
        crs: str = "EPSG:28992"
    ) -> PIL.Image:
        """Get climate layer as image overlay."""
        # Use WMS GetMap request
        # Return image for overlay in 3D viewer
```

### Use Cases

- **Woningbouwcorporaties:** ⭐⭐ Klimaatadaptatie (climate-proof design)
- **Gemeenten:** ⭐⭐⭐ Hittestress beleid (heat stress policy)
- **Projectontwikkelaars:** ⭐⭐ Future-proof design

### Recommendation: ✅ **HIGH PRIORITY - QUICK WIN**

**Rationale:**
- Standard OGC protocols (WMS/WFS)
- High policy relevance (climate adaptation)
- Free and open
- Good resolution (2m for heat data)
- Fits WMS provider architecture

**Implementation Strategy:**
1. Create service configuration (1 day)
2. Implement WMS provider (similar to WMTS) (1 day)
3. Test layer retrieval + CRS transformation (0.5 day)
4. Document climate use cases (0.5 day)

---

## GISKit Architecture Integration

### Current Architecture Strengths

✅ **Well-suited for external services:**

1. **Provider Pattern:** Clean abstraction for different data sources
2. **Protocol Support:** OGC Features, WFS, WMTS, WCS already implemented
3. **Config-driven:** YAML configs for services (see `giskit/config/services/`)
4. **Quirks System:** Handles service-specific oddities
5. **Async Support:** All providers use async/await
6. **CRS Handling:** Built-in coordinate transformation

### Integration Points

**Easy Integrations (1-2 days each):**
- Monumenten → Add to existing PDOK provider
- Klimaatatlas → Create WMS provider (similar to WMTS)

**Medium Integrations (3-4 days each):**
- OV Haltes → New provider, parse GTFS format
- Scholen → New provider + PDOK Locatieserver geocoding
- Energielabels → New provider + API key management

### Recommended File Structure

```
giskit/
  providers/
    ndov.py          # New: NDOV/OV Haltes
    duo.py           # New: DUO Schools
    ep_online.py     # New: EP-Online energy labels
    klimaateffectatlas.py  # New: Climate atlas WMS
    pdok.py          # Modified: add monumenten service

  config/
    services/
      ndov.yml       # New: NDOV GTFS configuration
      duo.yml        # New: DUO schools configuration
      ep-online.yml  # New: EP-Online configuration
      klimaateffectatlas.yml  # New: Climate layers
      pdok.yml       # Modified: add monumenten
```

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)

**Priority:** HIGH
**Effort:** 1 week
**Services:** 3 services

1. **Monumenten (2 hours)**
   - Add to PDOK config
   - Test WFS access
   - Document

2. **Klimaatatlas (2-3 days)**
   - Create WMS provider
   - Add service config
   - Test layer retrieval
   - Document climate use cases

3. **OV Haltes (2-3 days)**
   - Create NDOV provider
   - GTFS parsing
   - Spatial filtering
   - Documentation

**Deliverables:**
- 3 working providers
- Configuration files
- Usage examples
- Documentation

### Phase 2: Medium Complexity (Week 2)

**Priority:** MEDIUM
**Effort:** 1 week
**Services:** 2 services

4. **Scholen (3-4 days)**
   - Create DUO provider
   - PDOK Locatieserver integration
   - Geocoding + caching
   - Documentation

5. **Energielabels (3-4 days)**
   - Create EP-Online provider
   - API key management
   - Large file handling + caching
   - BAG ID matching
   - Documentation

**Deliverables:**
- 2 working providers
- Geocoding utilities
- Cache management
- API key documentation

### Phase 3: Polish & Testing (Week 3)

**Priority:** HIGH
**Effort:** 3-5 days

- Integration tests for all 5 providers
- Recipe examples combining multiple services
- Performance optimization
- Error handling improvements
- Complete documentation
- Example notebooks

---

## Cost-Benefit Analysis

### Development Costs

| Service | Days | Cost @ €500/day | Total |
|---------|------|-----------------|-------|
| Monumenten | 0.25 | €125 | €125 |
| Klimaatatlas | 2.5 | €1,250 | €1,250 |
| OV Haltes | 2.5 | €1,250 | €1,250 |
| Scholen | 3.5 | €1,750 | €1,750 |
| Energielabels | 3.5 | €1,750 | €1,750 |
| Testing & Docs | 3 | €1,500 | €1,500 |
| **TOTAL** | **15.25** | | **€7,625** |

### Operational Costs

**Ongoing costs:** €0/year

- All services are free
- No API fees
- No subscription costs
- Only requirement: EP-Online API key (free registration)

### Business Value

**Target Users:**
- Woningbouwcorporaties (housing corporations)
- Gemeenten (municipalities)
- Projectontwikkelaars (real estate developers)

**Use Cases:**
1. **Site feasibility analysis** - Quick assessment of location quality
2. **Climate-aware design** - Heat stress, flooding risk
3. **Social infrastructure** - Schools, transport accessibility
4. **Heritage constraints** - Monument proximity analysis
5. **Sustainability scoring** - Energy efficiency of existing stock

**ROI Estimate:**
- Development cost: €7,625
- Value per project analysis: €100-500 (time saved)
- Break-even: 15-75 project analyses
- Expected: 100+ analyses/year → **Strong positive ROI**

---

## Technical Risks & Mitigations

### Risk 1: API Availability Changes

**Risk:** External APIs may change URLs or authentication
**Likelihood:** Low-Medium
**Impact:** Medium

**Mitigation:**
- Monitor services with automated health checks
- Version service configs
- Document fallback strategies
- Subscribe to provider newsletters

### Risk 2: Data Quality Issues

**Risk:** Geocoding errors, missing data, outdated info
**Likelihood:** Medium
**Impact:** Low-Medium

**Mitigation:**
- Validate geocoded addresses (check confidence scores)
- Cache and version data
- Allow manual corrections
- Document data freshness

### Risk 3: Large File Downloads

**Risk:** EP-Online 300MB files, GTFS 258MB
**Likelihood:** High
**Impact:** Low

**Mitigation:**
- Implement smart caching (monthly for EP-Online, daily for GTFS)
- Use incremental updates (mutation files)
- Compress cached data
- Document disk space requirements

### Risk 4: API Key Management

**Risk:** EP-Online requires API key, user friction
**Likelihood:** Medium
**Impact:** Low

**Mitigation:**
- Clear documentation for registration
- Environment variable configuration
- Graceful error messages
- Optional: cache pre-downloaded data

---

## Recommendations

### ✅ Approve for Implementation

**All 5 services are recommended** for integration into GISKit.

### Priority Order

1. **HIGH PRIORITY (Week 1):**
   - Monumenten (2 hours) - Quick win
   - Klimaatatlas (2-3 days) - High policy value
   - OV Haltes (2-3 days) - High business value

2. **MEDIUM PRIORITY (Week 2):**
   - Scholen (3-4 days) - Requires geocoding
   - Energielabels (3-4 days) - Requires API key

3. **POLISH (Week 3):**
   - Testing, documentation, examples

### Success Criteria

- [ ] All 5 providers pass integration tests
- [ ] Documentation complete with examples
- [ ] Geocoding achieves >95% success rate
- [ ] Caching reduces download times by >80%
- [ ] Climate layers display correctly in viewers
- [ ] API key setup documented clearly

### Next Steps

1. **Approve roadmap** (this document)
2. **Begin Phase 1** (Monumenten, Klimaatatlas, OV Haltes)
3. **Test with real projects** (use curieweg recipes as examples)
4. **Gather feedback** from target users
5. **Iterate** based on usage patterns

---

## Appendix: Service Comparison Matrix

| Feature | OV Haltes | Scholen | Energielabels | Monumenten | Klimaatatlas |
|---------|-----------|---------|---------------|------------|--------------|
| **API Access** | Free | Free | Free + Key | Free | Free |
| **Update Freq** | Daily | Monthly | Monthly+Daily | Ongoing | Multiple/year |
| **Format** | GTFS/CSV | CSV | CSV/XML | WFS/GML | WMS/WFS |
| **Geocoding** | ✅ Included | ❌ Required | ✅ Has BAG ID | ✅ Included | ✅ Included |
| **Coverage** | National | National | National | National | National |
| **CRS** | WGS84 | Addresses | BAG IDs | RD | RD |
| **Size** | 258 MB | ~1 MB | 300 MB | WFS | WMS tiles |
| **Complexity** | Low | Medium | Medium | Low | Low |
| **Days to Implement** | 2-3 | 3-4 | 3-4 | 0.25 | 2-3 |
| **Business Value** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Technical Fit** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

**Document Status:** Ready for approval
**Prepared by:** GISKit Development Team
**Date:** November 24, 2025
