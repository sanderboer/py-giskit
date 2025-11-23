# API Quirks System Documentation

## Overzicht

GISKit gebruikt een **configuration-driven quirks system** om af te wijken van standaard API gedrag per provider. Dit maakt het mogelijk om provider-specifieke eigenaardigheden te handlen zonder de core protocol code te vervuilen.

## Waarom Quirks Nodig Zijn

Externe APIs volgen niet altijd de specificatie perfect. Voorbeelden:

### 1. **PDOK OGC API** - Meerdere Quirks
- ❌ **Probleem**: Vereist `?f=json` parameter (niet standaard OGC)
- ❌ **Probleem**: Gebruikt `v1_0` versienummering (underscore, niet punt)
- ❌ **Probleem**: Base URLs hebben trailing slash nodig voor `urljoin()`

### 2. **Andere Providers** (voorbeelden)
- API negeert `limit` parameter en returnt altijd max 5000 features
- API vereist custom `User-Agent` header
- API heeft langere timeouts nodig (>30s)
- API returnt 404 in plaats van lege collectie

---

## Architectuur

```
Provider Config
     ↓
  Quirks
     ↓
  Protocol
     ↓
  HTTP Request
```

### Componenten

**1. `ProtocolQuirks` Model** (`giskit/protocols/quirks.py`)
- Pydantic model met alle mogelijke quirks
- Methodes om quirks toe te passen op URLs, params, headers

**2. `KNOWN_QUIRKS` Registry**
- Centraal register van bekende provider quirks
- Per provider, per protocol

**3. `get_quirks()` Function**
- Helper om quirks op te halen voor provider/protocol combinatie
- Retourneert default quirks voor onbekende providers

**4. Protocol Integration**
- `OGCFeaturesProtocol` accepteert `quirks` parameter
- Past quirks automatisch toe bij requests

---

## Beschikbare Quirks

### URL Quirks

#### `requires_trailing_slash` (bool)
```python
ProtocolQuirks(requires_trailing_slash=True)

# Effect:
"https://api.example.com/v1" → "https://api.example.com/v1/"

# Waarom: Voorkomt urljoin() van "v1" te verwijderen
from urllib.parse import urljoin
urljoin("https://api.com/v1", "collections")   # ❌ "https://api.com/collections"
urljoin("https://api.com/v1/", "collections")  # ✅ "https://api.com/v1/collections"
```

### Request Parameter Quirks

#### `require_format_param` (bool)
```python
ProtocolQuirks(
    require_format_param=True,
    format_param_name="f",
    format_param_value="json"
)

# Effect: Voegt ?f=json toe aan alle requests
```

#### `max_features_limit` (int)
```python
ProtocolQuirks(max_features_limit=5000)

# Effect: Capt limit parameter
{"limit": 10000} → {"limit": 5000}
{"limit": 1000}  → {"limit": 1000}  # Blijft ongewijzigd
```

### Timeout Quirks

#### `custom_timeout` (float)
```python
ProtocolQuirks(custom_timeout=60.0)

# Effect: Override default timeout (meestal 30s)
```

### Header Quirks

#### `custom_headers` (dict)
```python
ProtocolQuirks(custom_headers={
    "User-Agent": "GISKit/1.0",
    "X-API-Key": "secret123"
})

# Effect: Voegt headers toe aan alle requests
```

### Response Quirks

#### `empty_collections_return_404` (bool)
```python
ProtocolQuirks(empty_collections_return_404=True)

# Effect: 404 wordt behandeld als lege response (niet error)
```

### Metadata Quirks

#### `description`, `issue_url`, `workaround_date`
```python
ProtocolQuirks(
    description="PDOK requires ?f=json parameter",
    issue_url="https://github.com/PDOK/issues/123",
    workaround_date="2024-11-22"
)

# Documentatie van waarom quirk nodig is
```

---

## Gebruik

### 1. Gebruik Bekende Quirks (AANBEVOLEN)

```python
from giskit.protocols.quirks import get_quirks
from giskit.protocols.ogc_features import OGCFeaturesProtocol

# Haal PDOK quirks op
quirks = get_quirks("pdok", "ogc-features")

# Maak protocol met quirks
protocol = OGCFeaturesProtocol(
    base_url="https://api.pdok.nl/lv/bgt/ogc/v1_0/",
    quirks=quirks
)

# Quirks worden automatisch toegepast!
```

### 2. Custom Quirks Definieren

```python
from giskit.protocols.quirks import ProtocolQuirks

quirks = ProtocolQuirks(
    requires_trailing_slash=True,
    require_format_param=True,
    format_param_name="format",
    format_param_value="geojson",
    custom_timeout=45.0,
    description="Custom API requires special format parameter"
)

protocol = OGCFeaturesProtocol(
    base_url="https://custom-api.com/data",
    quirks=quirks
)
```

### 3. Quirks Manueel Toepassen

```python
from giskit.protocols.quirks import ProtocolQuirks

quirks = ProtocolQuirks(require_format_param=True)

# URL
url = quirks.apply_to_url("https://api.com/v1")
# → "https://api.com/v1" (geen trailing slash quirk)

# Parameters
params = quirks.apply_to_params({"bbox": "1,2,3,4"})
# → {"bbox": "1,2,3,4", "f": "json"}

# Headers
headers = quirks.apply_to_headers({"Accept": "application/json"})
# → {"Accept": "application/json"}

# Timeout
timeout = quirks.get_timeout(30.0)
# → 30.0 (geen custom timeout)
```

---

## Nieuwe Provider Toevoegen

### Stap 1: Quirks Identificeren

Test de API en identificeer afwijkingen:

```bash
# Test zonder parameters
curl "https://new-api.com/collections"
# → 404? Misschien format param nodig

# Test met f=json
curl "https://new-api.com/collections?f=json"
# → 200 OK? Dan is quirk nodig!

# Test urljoin gedrag
python3 -c "
from urllib.parse import urljoin
print(urljoin('https://new-api.com/v1', 'collections'))
"
# → Verdwijnt 'v1'? Trailing slash nodig!
```

### Stap 2: Quirks Toevoegen aan Registry

```python
# giskit/protocols/quirks.py

KNOWN_QUIRKS = {
    "pdok": { ... },  # Bestaande
    "new-provider": {
        "ogc-features": ProtocolQuirks(
            requires_trailing_slash=True,
            require_format_param=True,
            format_param_name="outputFormat",
            format_param_value="application/json",
            custom_timeout=45.0,
            description="New Provider OGC API quirks",
            issue_url="https://github.com/provider/issues/456",
            workaround_date="2024-11-22"
        )
    }
}
```

### Stap 3: Provider Implementeren

```python
# giskit/providers/new_provider.py

from giskit.protocols.quirks import get_quirks

class NewProvider(Provider):
    def __init__(self, **kwargs):
        super().__init__("new-provider", **kwargs)
        
        # Haal quirks op
        quirks = get_quirks("new-provider", "ogc-features")
        
        # Registreer protocol met quirks
        protocol = OGCFeaturesProtocol(
            base_url="https://new-api.com/v1/",
            quirks=quirks
        )
        self.register_protocol("ogc-features", protocol)
```

### Stap 4: Tests Schrijven

```python
# tests/unit/test_new_provider_quirks.py

def test_new_provider_quirks():
    quirks = get_quirks("new-provider", "ogc-features")
    
    assert quirks.requires_trailing_slash is True
    assert quirks.require_format_param is True
    assert quirks.format_param_value == "application/json"
```

---

## Best Practices

### ✅ DO

1. **Documenteer quirks met metadata**
   ```python
   ProtocolQuirks(
       description="Waarom deze quirk nodig is",
       issue_url="Link naar bug report/docs",
       workaround_date="2024-11-22"
   )
   ```

2. **Test quirks expliciet**
   ```python
   def test_quirk_applied():
       quirks = get_quirks("provider", "protocol")
       params = quirks.apply_to_params({})
       assert params["f"] == "json"
   ```

3. **Gebruik centrale registry**
   ```python
   # ✅ GOED
   quirks = get_quirks("pdok", "ogc-features")
   
   # ❌ SLECHT
   quirks = ProtocolQuirks(...)  # Hardcoded in code
   ```

4. **Test met echte API**
   ```python
   # Integration test
   async def test_with_real_api():
       provider = get_provider("pdok")
       gdf = await provider.download_dataset(...)
       assert not gdf.empty
   ```

### ❌ DON'T

1. **Niet quirks hardcoden in protocol**
   ```python
   # ❌ SLECHT - in OGCFeaturesProtocol
   params["f"] = "json"  # PDOK-specific!
   
   # ✅ GOED - gebruik quirks
   params = self.quirks.apply_to_params(params)
   ```

2. **Niet quirks dupliceren**
   ```python
   # ❌ SLECHT - quirk op 2 plekken
   # pdok.py
   protocol = OGCFeaturesProtocol(...)
   protocol.add_param("f", "json")  # Hardcoded
   
   # ✅ GOED - quirk in registry
   quirks = get_quirks("pdok", "ogc-features")
   ```

3. **Niet quirks in provider logica**
   ```python
   # ❌ SLECHT
   class PDOKProvider:
       async def download(self, ...):
           if self.name == "pdok":
               params["f"] = "json"  # Quirk in business logic!
   
   # ✅ GOED - quirk in protocol
   protocol = OGCFeaturesProtocol(quirks=pdok_quirks)
   ```

---

## Testing

### Unit Tests

```bash
# Test alleen quirks
poetry run pytest tests/unit/test_quirks.py -v

# Test specifieke quirk
poetry run pytest tests/unit/test_quirks.py::TestProtocolQuirks::test_format_param_quirk -v
```

### Integration Tests

```bash
# Test PDOK met quirks
poetry run pytest tests/integration/test_sitedb_use_case.py::TestSitedbUseCase::test_download_bgt_pand_curieweg -v
```

### Coverage

```bash
poetry run pytest tests/ --cov=giskit.protocols.quirks --cov-report=html
# Open htmlcov/index.html
```

---

## Troubleshooting

### Probleem: Quirk wordt niet toegepast

**Symptoom**: API call faalt nog steeds

**Check**:
1. Is quirk geregistreerd in `KNOWN_QUIRKS`?
   ```python
   from giskit.protocols.quirks import KNOWN_QUIRKS
   print(KNOWN_QUIRKS["pdok"]["ogc-features"])
   ```

2. Wordt quirk correct opgehaald?
   ```python
   quirks = get_quirks("pdok", "ogc-features")
   print(quirks.require_format_param)  # True?
   ```

3. Wordt protocol met quirks gemaakt?
   ```python
   protocol = OGCFeaturesProtocol(..., quirks=quirks)
   print(protocol.quirks.require_format_param)  # True?
   ```

### Probleem: Quirk te breed toegepast

**Symptoom**: Andere providers krijgen PDOK quirks

**Oplossing**: Check provider-specific quirks:
```python
# ❌ FOUT
all_providers_use_quirks = ProtocolQuirks(...)

# ✅ GOED
quirks = get_quirks("pdok", "ogc-features")  # Alleen PDOK
```

### Probleem: URL nog steeds fout

**Symptoom**: `urljoin()` verwijdert nog steeds versie

**Check**:
1. Heeft base URL trailing slash?
   ```python
   print(protocol.base_url)  # Moet eindigen met /
   ```

2. Is quirk toegepast tijdens init?
   ```python
   quirks = ProtocolQuirks(requires_trailing_slash=True)
   url = "https://api.com/v1"
   fixed = quirks.apply_to_url(url)
   print(fixed)  # "https://api.com/v1/"
   ```

---

## Voorbeelden

### Voorbeeld 1: PDOK BGT Download

```python
from giskit.providers.base import get_provider
from giskit.core.recipe import Dataset, Location, LocationType

# Provider heeft al PDOK quirks geladen
provider = get_provider("pdok")

dataset = Dataset(provider="pdok", service="bgt", layers=["pand"])
location = Location(
    type=LocationType.BBOX,
    value=[4.32, 51.83, 4.34, 51.85]
)

# Quirks worden automatisch toegepast:
# - Base URL krijgt trailing slash
# - Alle requests krijgen ?f=json
gdf = await provider.download_dataset(dataset, location, ...)
```

### Voorbeeld 2: Custom Provider met Quirks

```python
from giskit.protocols.quirks import ProtocolQuirks
from giskit.protocols.ogc_features import OGCFeaturesProtocol

# Custom quirks voor langzame API
custom_quirks = ProtocolQuirks(
    requires_trailing_slash=True,
    custom_timeout=120.0,  # 2 minuten
    max_features_limit=1000,  # API kan niet meer aan
    custom_headers={"X-Client": "GISKit"},
    description="Slow API with strict limits"
)

protocol = OGCFeaturesProtocol(
    base_url="https://slow-api.com/data/",
    quirks=custom_quirks
)

# Protocol past alle quirks toe
async with protocol:
    gdf = await protocol.get_features(bbox=..., layers=...)
```

### Voorbeeld 3: Quirks Testen

```python
def test_my_provider_quirks():
    """Test custom provider quirks."""
    from giskit.protocols.quirks import get_quirks
    
    quirks = get_quirks("my-provider", "ogc-features")
    
    # Test URL fix
    url = quirks.apply_to_url("https://api.com/v2")
    assert url.endswith("/")
    
    # Test params
    params = quirks.apply_to_params({"bbox": "1,2,3,4"})
    assert "f" in params
    assert params["f"] == "json"
    
    # Test timeout
    timeout = quirks.get_timeout(30.0)
    assert timeout > 30.0  # Custom timeout
```

---

## Toekomstige Uitbreidingen

### 1. Auto-Detection (Optioneel)
```python
class OGCFeaturesProtocol(Protocol):
    async def _detect_quirks(self):
        """Auto-detect API quirks by probing."""
        # Try without f=json
        try:
            response = await self._client.get(url)
        except HTTPError:
            # Try with f=json
            response = await self._client.get(url, params={"f": "json"})
            if response.ok:
                self.quirks.require_format_param = True
```

### 2. Quirks van File Laden
```python
# config/quirks.yaml
providers:
  pdok:
    ogc-features:
      requires_trailing_slash: true
      require_format_param: true
      format_param_name: f
      format_param_value: json
```

### 3. Quirks Monitoring
```python
@dataclass
class QuirkUsage:
    provider: str
    quirk_type: str
    applied_count: int
    last_applied: datetime

# Track welke quirks het meest gebruikt worden
```

---

## Conclusie

Het **Configuration-Driven Quirks System** biedt:

✅ **Schaalbaarheid** - Nieuwe providers gemakkelijk toe te voegen  
✅ **Onderhoudbaarheid** - Quirks gecentral iseerd, niet verspreid  
✅ **Testbaarheid** - Quirks individueel testbaar  
✅ **Documentatie** - Metadata legt uit waarom quirks nodig zijn  
✅ **Flexibiliteit** - Custom quirks voor edge cases  

Dit maakt GISKit robuust tegen API eigenaardigheden zonder de core code te vervuilen.
