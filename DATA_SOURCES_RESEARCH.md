# Data Sources Research - Streaming APIs

Research on additional data providers with OGC-compliant streaming APIs for potential giskit integration.

**Research Date**: 2024-11-22  
**Status**: Initial survey

---

## Summary

| Region | Provider | Status | Priority |
|--------|----------|--------|----------|
| 🇳🇱 Netherlands | PDOK | ✅ **Integrated** (53 services) | ⭐⭐⭐ Complete |
| 🇧🇪 Belgium | Geo-Vlaanderen | 🟢 Ready to integrate | ⭐⭐⭐ High |
| 🇬🇧 UK | Ordnance Survey | 🟡 Requires API key | ⭐⭐ Medium |
| 🇩🇪 Germany | BKG | 🟡 To investigate | ⭐⭐ Medium |
| 🌍 Global | OpenStreetMap | 🟡 Different protocol | ⭐⭐⭐ High |
| 🌍 Global | NASA GIBS | 🟡 Imagery only | ⭐ Low |
| 🇪🇺 EU | INSPIRE | 🔴 Complex federation | ⭐ Low |

---

## 1. Belgium: Geo-Vlaanderen (Flanders)

### Overview
**Provider**: Informatie Vlaanderen (Flemish Government)  
**URL**: https://www.geopunt.be/  
**API Base**: https://geo.api.vlaanderen.be/  
**Coverage**: Flanders region (Belgium)  
**License**: Open data

### Protocols Available
- ✅ **WFS 2.0.0** - Vector features
- ✅ **WMTS** - Tile imagery
- ✅ **WMS** - Map rendering
- ✅ **WCS** - Coverage data

### Key Services

#### GRB (Grootschalig Referentiebestand)
**Base URL**: `https://geo.api.vlaanderen.be/GRB/wfs`

**Similar to**: Dutch BGT (Basisregistratie Grootschalige Topografie)

**Layers** (60+ feature types):
- Buildings (gebouwen): `GRB:Gbg` (gebouw aan de grond)
- Parcels (percelen): `GRB:Adp` (administratief perceel)
- Roads (wegen): `GRB:Wrg` (wegsegment)
- Addresses: `GRB:Adr` (adres)
- Terrain features: grass, water, construction
- Infrastructure: walls, fences, utilities

**Test Query**:
```bash
curl "https://geo.api.vlaanderen.be/GRB/wfs?service=WFS&version=2.0.0&request=GetCapabilities"
```

#### Other Services
- **CRAB**: Addresses and buildings (legacy, being replaced by GRB)
- **Bodemkaart**: Soil maps
- **Orthofoto**: Aerial imagery (WMTS)
- **DHM**: Digital Height Model (DTM/DSM similar to AHN)

### Integration Potential
**Difficulty**: ⭐ Easy (same tech as PDOK)  
**Value**: ⭐⭐⭐ High (Belgium coverage, similar quality to PDOK)  
**API Quality**: Excellent (WFS 2.0.0, GML 3.2, INSPIRE-compliant)

**Implementation**:
```python
# Can reuse OGCFeaturesProvider architecture
provider = OGCFeaturesProvider("geo-vlaanderen")
# Config: giskit/config/services/geo-vlaanderen.yml
```

**Next Steps**:
1. Create `geo-vlaanderen.yml` config file
2. Map GRB layer names to English equivalents
3. Test with Brussels/Antwerp sample area
4. Document Dutch→Flemish terminology differences

---

## 2. United Kingdom: Ordnance Survey

### Overview
**Provider**: Ordnance Survey Ltd  
**URL**: https://osdatahub.os.uk/  
**API Base**: https://api.os.uk/  
**Coverage**: United Kingdom  
**License**: Open data (OS OpenData) + Premium (requires license)

### Protocols Available
- ✅ **OGC API Features** - Modern vector API
- ✅ **WMTS** - Tile imagery
- ✅ **WFS** - Legacy vector API
- ✅ **WMS** - Map rendering

### Key Services

#### OS NGD (National Geographic Database)
**Base URL**: `https://api.os.uk/features/ngd/ofa/v1/`

**Collections** (OS NGD Features API):
- `bld-fts-buildingpart` - Building footprints
- `trn-rami-roadlink` - Road network
- `trn-rami-railwaylink` - Railway network
- `trn-fts-railwaystation` - Railway stations
- `nts-fts-namedplace` - Place names
- `lnd-fts-landcoverpart` - Land cover

#### OS Open Data (Free)
- **OS Open Roads**: Road network (shapefile format)
- **OS Open Rivers**: Water network
- **OS Open Greenspace**: Parks and green areas
- **OS Open Zoomstack**: Multi-scale basemap
- **Boundary-Line**: Administrative boundaries

### Authentication
⚠️ **Requires API Key** (free tier available)

**Free tier limits**:
- 6 requests/second
- API key required for all requests

**Example**:
```bash
curl "https://api.os.uk/features/ngd/ofa/v1/?key=YOUR_API_KEY"
```

### Integration Potential
**Difficulty**: ⭐⭐ Medium (requires API key management)  
**Value**: ⭐⭐⭐ High (UK coverage, official data)  
**API Quality**: Excellent (modern OGC API Features)

**Implementation Considerations**:
- Need API key storage (environment variables or config)
- Free tier sufficient for most use cases
- Premium data requires commercial license

**Next Steps**:
1. Create user documentation for API key setup
2. Add API key support to OGCFeaturesProvider
3. Create `ordnance-survey.yml` config
4. Test with London sample area

---

## 3. Germany: BKG (Federal Agency for Cartography)

### Overview
**Provider**: Bundesamt für Kartographie und Geodäsie  
**URL**: https://gdz.bkg.bund.de/  
**Coverage**: Germany  
**License**: Open data (most services)

### Services Available
- **VG250**: Administrative boundaries (Verwaltungsgebiete)
- **DOP**: Digital Orthophotos
- **DTK**: Digital topographic maps
- **DGM**: Digital terrain model

### Protocols
- ✅ WMS
- ✅ WMTS  
- ✅ WFS
- ✅ WCS (for elevation)

**Status**: Needs further investigation  
**Priority**: Medium (Germany coverage)

---

## 4. OpenStreetMap: Overpass API

### Overview
**Provider**: OpenStreetMap Foundation  
**URL**: https://overpass-api.de/  
**Coverage**: Global  
**License**: ODbL (Open Database License)

### Protocol
**Overpass QL** (custom query language, not OGC-compliant)

### Example Query
```
[out:json];
area["name"="Amsterdam"]->.a;
(
  node["amenity"="restaurant"](area.a);
  way["amenity"="restaurant"](area.a);
);
out center;
```

### Integration Potential
**Difficulty**: ⭐⭐⭐ Hard (custom protocol)  
**Value**: ⭐⭐⭐ Very High (global coverage, rich POI data)  
**API Quality**: Good (mature, well-documented)

**Implementation**:
- Requires custom `OverpassProtocol` class
- Not OGC-compliant
- Different query paradigm (tags, not layers)

**Next Steps**:
1. Research Overpass QL → GeoJSON conversion
2. Design `OverpassProvider` architecture
3. Create query builder for common use cases

---

## 5. NASA GIBS (Global Imagery Browse Services)

### Overview
**Provider**: NASA EOSDIS  
**URL**: https://www.earthdata.nasa.gov/eosdis/daacs/gibs  
**Coverage**: Global  
**License**: Public domain

### Protocol
- ✅ **WMTS** (tile imagery)
- ✅ **WMS** (dynamic maps)

### Data Products
- MODIS: Moderate Resolution Imaging Spectroradiometer
- VIIRS: Visible Infrared Imaging Radiometer Suite
- Landsat: Multispectral satellite imagery
- SRTM: Shuttle Radar Topography Mission (elevation)

### Integration Potential
**Difficulty**: ⭐ Easy (standard WMTS)  
**Value**: ⭐⭐ Medium (global imagery, but low resolution for site analysis)  
**Use case**: Background imagery, large-scale environmental analysis

**Implementation**:
- Can use existing WMTSProvider
- Add `nasa-gibs.yml` config
- Good for global context, not detailed site work

---

## 6. European Environment Agency (EEA)

### Overview
**Provider**: European Environment Agency  
**URL**: https://www.eea.europa.eu/data-and-maps  
**Coverage**: Europe  
**License**: Open data

### Services
- Air quality monitoring
- Land cover (Corine)
- Biodiversity indicators
- Water quality

### Protocols
- WMS, WFS (INSPIRE-compliant)

**Status**: Environmental/thematic data (not base mapping)  
**Priority**: Low for sitedb use cases

---

## 7. INSPIRE Geoportal (EU)

### Overview
**Provider**: European Commission  
**URL**: https://inspire-geoportal.ec.europa.eu/  
**Coverage**: All EU member states  
**License**: Varies by member state

### Challenge
- **Federated system** (links to national portals)
- Not a single API endpoint
- Requires per-country configuration
- Quality varies by country

**Status**: Complex, better to target national portals directly  
**Priority**: Low (prefer direct national sources)

---

## Recommendations

### High Priority (Next to Implement)

1. **🇧🇪 Geo-Vlaanderen (Belgium)**
   - ✅ Ready to integrate
   - ✅ No API key required
   - ✅ Excellent data quality
   - ✅ Same tech stack as PDOK
   - **Effort**: 2-3 days
   - **Value**: Full Belgium coverage

2. **🌍 OpenStreetMap Overpass**
   - Global POI coverage
   - Complements official datasets
   - **Effort**: 1-2 weeks (custom protocol)
   - **Value**: Global coverage, rich amenity data

### Medium Priority

3. **🇬🇧 Ordnance Survey (UK)**
   - Modern OGC API Features
   - Requires API key management
   - **Effort**: 3-4 days
   - **Value**: UK official data

4. **🇩🇪 BKG (Germany)**
   - Investigate service offerings
   - **Effort**: TBD
   - **Value**: Germany coverage

### Lower Priority

5. **🌍 NASA GIBS** - Background imagery only
6. **🇪🇺 EEA** - Thematic/environmental data
7. **🇪🇺 INSPIRE** - Too complex, prefer national sources

---

## Implementation Roadmap

### Phase 1: Belgium Integration (Week 1-2)
- [ ] Create `geo-vlaanderen.yml` service config
- [ ] Test GRB WFS endpoints
- [ ] Map Flemish layer names to English
- [ ] Add Brussels test case
- [ ] Update documentation

### Phase 2: OSM Overpass (Week 3-5)
- [ ] Research Overpass QL syntax
- [ ] Create `OverpassProtocol` class
- [ ] Build query generator
- [ ] Test with Amsterdam POIs
- [ ] Add rate limiting

### Phase 3: UK Ordnance Survey (Week 6-7)
- [ ] Add API key support to OGCFeaturesProvider
- [ ] Create `ordnance-survey.yml` config
- [ ] Document API key setup process
- [ ] Test with London area
- [ ] Handle free tier limits

---

## Technical Notes

### API Key Management Strategy

For providers requiring authentication (OS, NASA):

```yaml
# ~/.giskit/config/credentials.yml
providers:
  ordnance-survey:
    api_key: "${OS_API_KEY}"  # Read from environment variable
  
  nasa-gibs:
    api_key: "${NASA_API_KEY}"  # Optional
```

### Multi-Provider Queries

Future enhancement: Query multiple providers simultaneously:

```python
# Download buildings from best available source per region
recipe = {
    "location": bbox_europe,
    "datasets": [
        {"provider": "auto", "layers": ["buildings"]}
    ]
}

# Auto-selects:
# - Netherlands → PDOK BAG
# - Belgium → Geo-Vlaanderen GRB
# - UK → Ordnance Survey NGD
# - Rest → OpenStreetMap
```

---

## Excluded Sources

### RIVM Atlas Natuurlijk Kapitaal
**Reason**: Bulk downloads only, no streaming API  
**Alternative**: Download manually if needed

### Natural Earth
**Reason**: Static dataset, no API  
**Alternative**: Include as bundled resource for global base maps

### Copernicus Open Access Hub
**Reason**: Large satellite imagery, different use case  
**Alternative**: Out of scope for site-level analysis

---

**Next Action**: Implement Geo-Vlaanderen (Belgium) integration as proof-of-concept for multi-country support.
