# GISKit Config-Driven Architecture

Dit document beschrijft de **config-driven** architectuur van giskit en de MultiProtocolProvider implementatie.

## Current Architecture (November 2025)

### MultiProtocolProvider - Unified Provider System ✅ IMPLEMENTED

**Status**: ✅ Fully implemented and working with PDOK (52 services), BAG3D (1 service), NDOV (1 service)

The MultiProtocolProvider is a flexible, config-driven provider that supports multiple protocols per provider from a single YAML configuration file.

#### Architecture

```
Provider Config (YAML)
    ↓
MultiProtocolProvider
    ├── Service Discovery
    ├── Protocol Routing (per service)
    └── Dataset Download
         ↓
    Protocol Handlers
         ├── OGC Features
         ├── WMTS
         ├── WCS
         └── GTFS
```

#### Configuration Format

```yaml
# config/providers/pdok.yml
provider:
  name: "PDOK"
  title: "PDOK - Publieke Dienstverlening Op de Kaart"
  description: "Dutch national spatial data infrastructure"
  homepage: "https://www.pdok.nl"
  coverage: "Netherlands"

services:
  bgt:
    title: "Basisregistratie Grootschalige Topografie"
    url: "https://api.pdok.nl/lv/bgt/ogc/v1_0/"
    protocol: "ogc-features"  # ← Protocol specified per service
    category: "base_registers"
    keywords: [bgt, topografie, gebouwen]

  ahn:
    title: "Actueel Hoogtebestand Nederland"
    url: "https://service.pdok.nl/rws/ahn/wcs/v1_0"
    protocol: "wcs"  # ← Different protocol, same provider
    category: "elevation"
    keywords: [ahn, elevation, dtm, dsm]
```

#### Key Features

1. **Single Config File**: One YAML per provider with all services
2. **Per-Service Protocol**: Each service specifies its own protocol
3. **Auto-Discovery**: Providers automatically discovered from `config/providers/*.yml`
4. **Protocol Routing**: Requests routed to appropriate protocol handler based on service
5. **Catalog Integration**: Full metadata available for search and discovery

#### Implementation Details

Location: `giskit/providers/multi_protocol.py`

```python
class MultiProtocolProvider(Provider):
    """Unified provider supporting multiple protocols from single config."""

    def __init__(self, name: str, config_file: Path, **kwargs):
        # Load unified config
        self.config = load_yaml(config_file)
        self.services = self.config["services"]

        # Create protocol instances per service
        for service_id, service_config in self.services.items():
            protocol = service_config["protocol"]
            self._init_protocol(service_id, protocol, service_config)

    async def download_dataset(self, dataset, location, ...):
        # Route to appropriate protocol based on service
        service_id = dataset.service
        protocol = self._get_protocol(service_id)
        return await protocol.get_features(...)
```

#### Provider Discovery

Location: `giskit/config/discovery.py`

```python
def discover_providers(config_dir: Path) -> dict[str, dict]:
    """Auto-discover providers from config/providers/*.yml

    Detects:
    - Unified format: pdok.yml (NEW, preferred)
    - Split format: pdok/ogc-features.yml (LEGACY, supported)
    """
```

Discovery checks for:
1. **Unified format**: `providers/*.yml` with `provider` and `services` keys
2. **Legacy format**: `providers/{name}/{protocol}.yml` directories

### Service Catalog System ✅ IMPLEMENTED

**Location**: `giskit/catalog.py`

Provides discovery API for all available services across all providers.

#### API Functions

```python
from giskit.catalog import (
    list_all_services,      # Browse all providers
    search_services,        # Full-text search
    list_services_by_category,  # Filter by category
    list_services_by_protocol,  # Filter by protocol
    print_catalog,          # Pretty-print overview
    export_catalog_json,    # Export metadata
)
```

#### Usage Examples

```python
# List all services
catalog = list_all_services(detailed=True)
# {
#     "pdok": {
#         "title": "PDOK - ...",
#         "service_count": 52,
#         "protocols": ["ogc-features", "wcs", "wmts"],
#         "services": {"bgt": {...}, "ahn": {...}}
#     },
#     "ndov": {...},
#     "bag3d": {...}
# }

# Search for services
results = search_services("elevation")
# {"pdok": [{"id": "ahn", "title": "...", "relevance": 0.95}]}

# Filter by category
infrastructure = list_services_by_category("infrastructure")
# {"ndov": [{"id": "haltes", "title": "OV Haltes", ...}]}

# Export for external tools
export_catalog_json("catalog.json")
```

### Protocol System

#### Available Protocols

1. **OGC Features** (`ogc-features`) - Vector data via OGC API Features
2. **WMTS** (`wmts`) - Pre-rendered raster tiles
3. **WCS** (`wcs`) - Coverage data (elevation, raster)
4. **GTFS** (`gtfs`) - Public transport data (NEW)

#### Protocol Registration

```python
# giskit/protocols/__init__.py
from giskit.protocols.ogc_features import OGCFeaturesProtocol
from giskit.protocols.wmts import WMTSProtocol
from giskit.protocols.wcs import WCSProtocol
from giskit.protocols.gtfs import GTFSProtocol  # NEW

# Each protocol implements Protocol base class
```

### Provider Types

#### 1. MultiProtocolProvider (Config-Driven)

**Used by**: PDOK, BAG3D
**Config**: Single YAML with all services
**Protocols**: Multiple per provider

```yaml
# config/providers/pdok.yml
services:
  bgt:
    protocol: ogc-features
  ahn:
    protocol: wcs
  luchtfoto:
    protocol: wmts
```

#### 2. Single-Protocol Providers (Code-Based)

**Used by**: NDOV (GTFS)
**Implementation**: Direct Python class
**Protocols**: One per provider

```python
# giskit/providers/gtfs.py
class GTFSProvider(Provider):
    """Provider for GTFS public transport data."""

    def __init__(self, name: str, gtfs_url: str = None, **kwargs):
        # Load gtfs_url from config if not provided
        if gtfs_url is None:
            config = get_provider_config(name)
            gtfs_url = load_yaml(config["config_file"])["gtfs_url"]

        self.protocol = GTFSProtocol(base_url=gtfs_url, cache_days=1)
```

#### Provider Registration

Providers can be registered in two ways:

1. **Auto-Discovery** (Preferred): Place config in `config/providers/{name}.yml`
2. **Explicit Registration**: Call `register_provider(name, ProviderClass)` at module level

```python
# Auto-discovered (PDOK, BAG3D)
# config/providers/pdok.yml exists → Automatically available

# Explicitly registered (NDOV)
from giskit.providers.base import register_provider
register_provider("ndov", GTFSProvider)
```

### Data Flow

```
User Recipe (JSON)
    ↓
Recipe Parser
    ↓
Provider Factory (get_provider)
    ├─→ Auto-discover from config
    └─→ Check explicit registrations
         ↓
Provider Instance
    ├─→ MultiProtocolProvider (for PDOK, BAG3D)
    └─→ GTFSProvider (for NDOV)
         ↓
Protocol Handler
    ├─→ OGCFeaturesProtocol
    ├─→ WMTSProtocol
    ├─→ WCSProtocol
    └─→ GTFSProtocol
         ↓
Downloaded GeoDataFrame
```

### Supported Providers

| Provider | Services | Protocols | Format | Status |
|----------|----------|-----------|---------|--------|
| **PDOK** | 52 | ogc-features, wcs, wmts | Unified YAML | ✅ Working |
| **BAG3D** | 1 | ogc-features | Unified YAML | ✅ Working |
| **NDOV** | 1 | gtfs | Unified YAML + Python | ✅ Working |

---

## Legacy Documentation (Pre-MultiProtocolProvider)

### Oude Situatie (Voor November 2025)

**Probleem**: Services en quirks zijn hardcoded in Python bestanden.

```python
# giskit/providers/pdok.py - 600+ lines
PDOK_SERVICES = {
    "bgt": {"url": "...", "title": "...", ...},  # 48x herhalen
}

# giskit/protocols/quirks.py - 300+ lines
KNOWN_QUIRKS = {
    "pdok": ProtocolQuirks(...),
    "cityjson": ProtocolQuirks(...),
}
```

**Nadelen**:
- ❌ Code change nodig om service toe te voegen
- ❌ Moeilijk te delen tussen tools (Python, CLI, docs)
- ❌ Geen validatie van service definitions
- ❌ Git diffs zijn groot en onduidelijk
- ❌ Gebruikers kunnen geen eigen providers toevoegen

## Toekomstige Architectuur (Config-Driven)

### Fase 1: Extract to Config Files ✅ (Ontwerp klaar)

```yaml
# config/services/pdok.yml
provider:
  name: pdok
  title: PDOK
  country: NL

defaults:
  quirks: [pdok-ogc]
  timeout: 10.0

services:
  bgt:
    url: https://api.pdok.nl/lv/bgt/ogc/v1_0/
    title: Basisregistratie Grootschalige Topografie
    category: base_registers
    keywords: [bgt, topografie, gebouwen]
```

```yaml
# config/quirks/providers.yml
pdok-ogc:
  requires_trailing_slash: true
  require_format_param: true
  format_param_name: f
  format_param_value: json
  description: PDOK OGC API quirks
```

### Fase 2: Generic Config Loaders

```python
# giskit/config/loader.py
from giskit.config import load_services, load_quirks

# Load any provider
services = load_services("pdok")  # From config/services/pdok.yml
services = load_services("custom", path="/my/custom.yml")

# Load quirks
quirks = load_quirks()
```

### Fase 3: Backward Compatibility

```python
# giskit/providers/pdok.py
from giskit.config import load_services

# Auto-load from config, fallback to hardcoded
PDOK_SERVICES = load_services("pdok", fallback=LEGACY_SERVICES)
```

### Fase 4: User Configs

```bash
# Users can add their own providers
cat > ~/.giskit/services/my-provider.yml <<EOF
services:
  my-service:
    url: https://my-api.com/ogc/v1/
    title: My Custom Service
EOF

# Monitor custom services
python -m giskit.indexer check-all --config ~/.giskit/services/my-provider.yml
```

## Voordelen

### Voor Developers

1. **Minder code** - Services zijn data, niet code
2. **Betere tests** - Config validatie ipv Python tests
3. **Snellere development** - Geen code changes voor nieuwe services

### Voor Users

1. **Eigen services toevoegen** zonder code te wijzen
2. **Configs delen** met team/community
3. **Version control** van service catalogs
4. **Validatie** voordat deployen

### Voor Maintenance

1. **Auto-update** van services via config syncs
2. **Deprecation warnings** via config metadata
3. **Service marketplace** mogelijk (install community configs)

## Implementatie Plan

### ✅ Done (Nu)

- [x] Architectuur ontwerp
- [x] Config directory structure
- [x] README documentatie
- [x] Visie document (dit bestand)

### 🔄 Todo (Toekomst)

**Phase 1: Config Files** (Prioriteit: Medium)
- [ ] Export PDOK_SERVICES naar `config/services/pdok.yml`
- [ ] Export KNOWN_QUIRKS naar `config/quirks/*.yml`
- [ ] JSON Schema voor validatie

**Phase 2: Config Loaders** (Prioriteit: Medium)
- [ ] `giskit.config.load_services()`
- [ ] `giskit.config.load_quirks()`
- [ ] Caching & performance

**Phase 3: Integration** (Prioriteit: Low)
- [ ] Update providers to use loaders
- [ ] Update monitor to use loaders
- [ ] Backward compatibility tests

**Phase 4: User Features** (Prioriteit: Low)
- [ ] User config directory `~/.giskit/`
- [ ] Config validation CLI
- [ ] Config marketplace (stretch goal)

## Waarom Niet Nu?

**Huidige systeem werkt goed**:
- ✅ 48 services werken
- ✅ Quirks systeem werkt
- ✅ Monitor werkt
- ✅ Tests passen

**Config-driven is een verbetering, maar niet kritisch**:
- Kan later zonder breaking changes
- Backward compatibility mogelijk
- Incrementele migratie mogelijk

## Wanneer Wel?

**Triggers voor config refactoring**:
1. **> 100 services** - Hardcoded wordt te groot
2. **Multiple providers** - Als we meer dan PDOK ondersteunen
3. **Community requests** - Als users eigen services willen toevoegen
4. **Auto-sync** - Als we automatische updates willen

## Conclusie

**Nu**: Hardcoded werkt prima voor 48 PDOK services
**Toekomst**: Config-driven als we groeien
**Strategie**: Documenteer visie, implementeer later indien nodig

**Aanbeveling**: Laat huidige implementatie staan, dit document dient als blueprint voor toekomstige refactoring.

---

**Status**: 📋 Ontwerp klaar, implementatie geparkeerd
**Priority**: Low (nice-to-have, niet kritisch)
**Effort**: ~2-3 dagen werk voor volledige migratie
**Risk**: Low (backward compatibility mogelijk)
