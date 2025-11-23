# API Quirks System Documentation

## Overview

GISKit uses a **configuration-driven quirks system** to deviate from standard API behavior per provider. This makes it possible to handle provider-specific quirks without polluting the core protocol code.

## Why Quirks Are Needed

Externe APIs volgen niet altijd de specificatie perfect. Examples:

### 1. **PDOK OGC API** - Multiple Quirks
- ❌ **Problem**: Requires `?f=json` parameter (not standard OGC)
- ❌ **Problem**: Usaget `v1_0` versienummering (underscore, not dot)
- ❌ **Problem**: Base URLs need trailing slash for `urljoin()`

### 2. **Other Providers** (examples)
- API ignores `limit` parameter en always returns max 5000 features
- API requires custom `User-Agent` header
- API needs longer timeouts (>30s)
- API returns 404 instead of empty collection

---

## Architecture

```
Provider Config
     ↓
  Quirks
     ↓
  Protocol
     ↓
  HTTP Request
```

### Components

**1. `ProtocolQuirks` Model** (`giskit/protocols/quirks.py`)
- Pydantic model with all possible quirks
- Methods to apply quirks to URLs, params, headers

**2. `KNOWN_QUIRKS` Registry**
- Central registry of known provider quirks
- Per provider, per protocol

**3. `get_quirks()` Function**
- Helper to retrieve quirks for provider/protocol combination
- Returns default quirks for unknown providers

**4. Protocol Integration**
- `OGCFeaturesProtocol` accepts `quirks` parameter
- Applies quirks automatically on requests

---

## Available Quirks

### URL Quirks

#### `requires_trailing_slash` (bool)
```python
ProtocolQuirks(requires_trailing_slash=True)

# Effect:
"https://api.example.com/v1" → "https://api.example.com/v1/"

# Why: Prevents urljoin() from removing "v1" 
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

# Effect: Adds ?f=json to all requests
```

#### `max_features_limit` (int)
```python
ProtocolQuirks(max_features_limit=5000)

# Effect: Caps limit parameter
{"limit": 10000} → {"limit": 5000}
{"limit": 1000}  → {"limit": 1000}  # Remains unchanged
```

### Timeout Quirks

#### `custom_timeout` (float)
```python
ProtocolQuirks(custom_timeout=60.0)

# Effect: Override default timeout (usually 30s)
```

### Header Quirks

#### `custom_headers` (dict)
```python
ProtocolQuirks(custom_headers={
    "User-Agent": "GISKit/1.0",
    "X-API-Key": "secret123"
})

# Effect: Adds headers to all requests
```

### Response Quirks

#### `empty_collections_return_404` (bool)
```python
ProtocolQuirks(empty_collections_return_404=True)

# Effect: 404 is treated as empty response (not error)
```

### Metadata Quirks

#### `description`, `issue_url`, `workaround_date`
```python
ProtocolQuirks(
    description="PDOK requires ?f=json parameter",
    issue_url="https://github.com/PDOK/issues/123",
    workaround_date="2024-11-22"
)

# Documentation of why quirk is needed
```

---

## Usage

### 1. Usage Bekende Quirks (RECOMMENDED)

```python
from giskit.protocols.quirks import get_quirks
from giskit.protocols.ogc_features import OGCFeaturesProtocol

# Get PDOK quirks
quirks = get_quirks("pdok", "ogc-features")

# Create protocol with quirks
protocol = OGCFeaturesProtocol(
    base_url="https://api.pdok.nl/lv/bgt/ogc/v1_0/",
    quirks=quirks
)

# Quirks are applied automatically!
```

### 2. Define Custom Quirks

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

### 3. Manually Apply Quirks

```python
from giskit.protocols.quirks import ProtocolQuirks

quirks = ProtocolQuirks(require_format_param=True)

# URL
url = quirks.apply_to_url("https://api.com/v1")
# → "https://api.com/v1" (no trailing slash quirk)

# Parameters
params = quirks.apply_to_params({"bbox": "1,2,3,4"})
# → {"bbox": "1,2,3,4", "f": "json"}

# Headers
headers = quirks.apply_to_headers({"Accept": "application/json"})
# → {"Accept": "application/json"}

# Timeout
timeout = quirks.get_timeout(30.0)
# → 30.0 (no custom timeout)
```

---

## Adding New Provider

### Step 1: Identify Quirks

Test the API and identify deviations:

```bash
# Test without parameters
curl "https://new-api.com/collections"
# → 404? Maybe format param needed

# Test with f=json
curl "https://new-api.com/collections?f=json"
# → 200 OK? Then quirk is needed!

# Test urljoin behavior
python3 -c "
from urllib.parse import urljoin
print(urljoin('https://new-api.com/v1', 'collections'))
"
# → Disappears 'v1'? Trailing slash needed!
```

### Step 2: Add Quirks to Registry

```python
# giskit/protocols/quirks.py

KNOWN_QUIRKS = {
    "pdok": { ... },  # Existing
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

### Step 3: Implement Provider

```python
# giskit/providers/new_provider.py

from giskit.protocols.quirks import get_quirks

class NewProvider(Provider):
    def __init__(self, **kwargs):
        super().__init__("new-provider", **kwargs)
        
        # Get quirks
        quirks = get_quirks("new-provider", "ogc-features")
        
        # Register protocol with quirks
        protocol = OGCFeaturesProtocol(
            base_url="https://new-api.com/v1/",
            quirks=quirks
        )
        self.register_protocol("ogc-features", protocol)
```

### Step 4: Write Tests

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

1. **Document quirks with metadata**
   ```python
   ProtocolQuirks(
       description="Why this quirk is needed",
       issue_url="Link to bug report/docs",
       workaround_date="2024-11-22"
   )
   ```

2. **Test quirks explicitly**
   ```python
   def test_quirk_applied():
       quirks = get_quirks("provider", "protocol")
       params = quirks.apply_to_params({})
       assert params["f"] == "json"
   ```

3. **Usage centrale registry**
   ```python
   # ✅ GOOD
   quirks = get_quirks("pdok", "ogc-features")
   
   # ❌ BAD
   quirks = ProtocolQuirks(...)  # Hardcoded in code
   ```

4. **Test with echte API**
   ```python
   # Integration test
   async def test_with_real_api():
       provider = get_provider("pdok")
       gdf = await provider.download_dataset(...)
       assert not gdf.empty
   ```

### ❌ DON'T

1. **Don't hardcode quirks in protocol**
   ```python
   # ❌ BAD - in OGCFeaturesProtocol
   params["f"] = "json"  # PDOK-specific!
   
   # ✅ GOOD - use quirks
   params = self.quirks.apply_to_params(params)
   ```

2. **Don't duplicate quirks**
   ```python
   # ❌ BAD - quirk in 2 places
   # pdok.py
   protocol = OGCFeaturesProtocol(...)
   protocol.add_param("f", "json")  # Hardcoded
   
   # ✅ GOOD - quirk in registry
   quirks = get_quirks("pdok", "ogc-features")
   ```

3. **Don't put quirks in provider logic**
   ```python
   # ❌ BAD
   class PDOKProvider:
       async def download(self, ...):
           if self.name == "pdok":
               params["f"] = "json"  # Quirk in business logic!
   
   # ✅ GOOD - quirk in protocol
   protocol = OGCFeaturesProtocol(quirks=pdok_quirks)
   ```

---

## Testing

### Unit Tests

```bash
# Test quirks only
poetry run pytest tests/unit/test_quirks.py -v

# Test specific quirk
poetry run pytest tests/unit/test_quirks.py::TestProtocolQuirks::test_format_param_quirk -v
```

### Integration Tests

```bash
# Test PDOK with quirks
poetry run pytest tests/integration/test_sitedb_use_case.py::TestSitedbUseCase::test_download_bgt_pand_curieweg -v
```

### Coverage

```bash
poetry run pytest tests/ --cov=giskit.protocols.quirks --cov-report=html
# Open htmlcov/index.html
```

---

## Troubleshooting

### Problem: Quirk wordt niet toegepast

**Symptoom**: API call still fails

**Check**:
1. Is quirk registered in `KNOWN_QUIRKS`?
   ```python
   from giskit.protocols.quirks import KNOWN_QUIRKS
   print(KNOWN_QUIRKS["pdok"]["ogc-features"])
   ```

2. Is quirk retrieved correctly?
   ```python
   quirks = get_quirks("pdok", "ogc-features")
   print(quirks.require_format_param)  # True?
   ```

3. Is protocol created with quirks?
   ```python
   protocol = OGCFeaturesProtocol(..., quirks=quirks)
   print(protocol.quirks.require_format_param)  # True?
   ```

### Problem: Quirk applied too broadly

**Symptoom**: Other providers get PDOK quirks

**Oplossing**: Check provider-specific quirks:
```python
# ❌ WRONG
all_providers_use_quirks = ProtocolQuirks(...)

# ✅ GOOD
quirks = get_quirks("pdok", "ogc-features")  # PDOK only
```

### Problem: URL still wrong

**Symptoom**: `urljoin()` still removes version

**Check**:
1. Does base URL have trailing slash?
   ```python
   print(protocol.base_url)  # Must end with /
   ```

2. Is quirk applied during init?
   ```python
   quirks = ProtocolQuirks(requires_trailing_slash=True)
   url = "https://api.com/v1"
   fixed = quirks.apply_to_url(url)
   print(fixed)  # "https://api.com/v1/"
   ```

---

## Examples

### Example 1: PDOK BGT Download

```python
from giskit.providers.base import get_provider
from giskit.core.recipe import Dataset, Location, LocationType

# Provider already has PDOK quirks loaded
provider = get_provider("pdok")

dataset = Dataset(provider="pdok", service="bgt", layers=["pand"])
location = Location(
    type=LocationType.BBOX,
    value=[4.32, 51.83, 4.34, 51.85]
)

# Quirks are applied automatically:
# - Base URL gets trailing slash
# - All requests get ?f=json
gdf = await provider.download_dataset(dataset, location, ...)
```

### Example 2: Custom Provider met Quirks

```python
from giskit.protocols.quirks import ProtocolQuirks
from giskit.protocols.ogc_features import OGCFeaturesProtocol

# Custom quirks for slow API
custom_quirks = ProtocolQuirks(
    requires_trailing_slash=True,
    custom_timeout=120.0,  # 2 minutes
    max_features_limit=1000,  # API cannot handle more
    custom_headers={"X-Client": "GISKit"},
    description="Slow API with strict limits"
)

protocol = OGCFeaturesProtocol(
    base_url="https://slow-api.com/data/",
    quirks=custom_quirks
)

# Protocol applies all quirks
async with protocol:
    gdf = await protocol.get_features(bbox=..., layers=...)
```

### Example 3: Test Quirks

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

## Future Extensions

### 1. Auto-Detection (Optional)
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

### 2. Load Quirks from File
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

# Track which quirks are used most
```

---

## Conclusion

The **Configuration-Driven Quirks System** provides:

✅ **Scalability** - New providers easy to add  
✅ **Maintainability** - Quirks gecentral iseerd, niet verspreid  
✅ **Testability** - Quirks individually testable  
✅ **Documentation** - Metadata explains why quirks are needed  
✅ **Flexibility** - Custom quirks for edge cases  

This makes GISKit robust against API quirks without polluting the core code.
