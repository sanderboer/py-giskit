# GISKit Configuration Files

Configuration files for services, providers, and API quirks.

## Directory Structure

```
config/
├── services/          # Service definitions per provider
│   ├── pdok.yml      # PDOK services (Netherlands)
│   └── example.yml   # Template for new providers
├── quirks/           # API quirk definitions
│   ├── protocols.yml # Protocol-level quirks (OGC, etc.)
│   ├── formats.yml   # Format-level quirks (CityJSON, etc.)
│   └── providers.yml # Provider-specific quirks
└── README.md         # This file
```

## Config-Driven Architecture

**Philosophy**: Keep code generic, put specifics in config files.

### Why Config Files?

**Before** (hardcoded):
```python
PDOK_SERVICES = {
    "bgt": {
        "url": "https://api.pdok.nl/lv/bgt/ogc/v1_0/",
        "title": "BGT",
        # ... 40+ more services
    }
}
```

**Issues**:
- ❌ Need code change to add service
- ❌ Can't share configs between tools
- ❌ Hard to validate/lint
- ❌ No version control friendly diffs

**After** (config-driven):
```yaml
# config/services/pdok.yml
services:
  bgt:
    url: https://api.pdok.nl/lv/bgt/ogc/v1_0/
    title: Basisregistratie Grootschalige Topografie
```

**Benefits**:
- ✅ Add services without code changes
- ✅ Share configs between Python/CLI/docs
- ✅ Easy validation with JSON schema
- ✅ Clean git diffs per service
- ✅ Users can add their own providers

## Usage

### Loading Services

```python
from giskit.config import load_services

# Load all PDOK services
services = load_services("pdok")

# Load custom provider
services = load_services("custom", config_dir="/path/to/configs")
```

### Loading Quirks

```python
from giskit.config import load_quirks

# Load all quirks
quirks = load_quirks()

# Get quirks for specific provider
pdok_quirks = quirks.get_provider_quirks("pdok")
cityjson_quirks = quirks.get_format_quirks("cityjson")
```

### Monitoring

```bash
# Monitor PDOK services (from config)
python -m giskit.indexer check-all --provider pdok

# Monitor custom services
python -m giskit.indexer check-all --config /path/to/custom.yml
```

## File Formats

### Service Definition (`config/services/*.yml`)

```yaml
# Metadata
provider:
  name: pdok
  title: PDOK - Publieke Dienstverlening Op de Kaart
  country: NL
  homepage: https://www.pdok.nl
  license: CC0-1.0

# Default quirks for all services
defaults:
  quirks:
    - pdok-ogc  # Apply to all services
  timeout: 10.0

# Services
services:
  service-id:
    url: https://api.example.com/
    title: Human readable title
    category: base_registers  # or: topography, statistics, etc.
    description: Detailed description
    keywords: [keyword1, keyword2]

    # Optional overrides
    quirks: [pdok-ogc, custom-quirk]  # Override defaults
    timeout: 30.0  # Override default timeout
    format: cityjson  # Data format (adds format quirks)

    # Metadata
    collections: 49  # Number of collections (auto-detected)
    last_checked: 2025-11-22  # Last health check
    status: healthy  # healthy | deprecated | moved
```

### Quirk Definition (`config/quirks/*.yml`)

```yaml
# Protocol quirks (OGC Features, WFS, etc.)
protocols:
  ogc-features-format-param:
    name: OGC Features Format Parameter
    applies_to: [ogc-features]
    require_format_param: true
    format_param_name: f
    format_param_value: json
    description: Some OGC servers require explicit format parameter

# Format quirks (CityJSON, GeoJSON, etc.)
formats:
  cityjson-v2:
    name: CityJSON 2.0 Transform Quirks
    format_is_cityjson: true
    cityjson_version: "2.0"
    has_per_page_transform: true
    transform_applies_to_vertices: true
    vertices_are_integers: true
    description: |
      CRITICAL: CityJSON uses per-page transforms for vertex compression.
      Each pagination page has different scale/translate values.
    references:
      - https://www.cityjson.org/specs/2.0.0/#transform-object

# Provider quirks (PDOK, Kadaster, etc.)
providers:
  pdok-trailing-slash:
    name: PDOK Trailing Slash Requirement
    requires_trailing_slash: true
    description: PDOK URLs must end with / to prevent urljoin issues
    workaround_date: "2024-11-22"
```

## Adding New Providers

1. **Create config file**: `config/services/your-provider.yml`
2. **Define services** following the schema above
3. **Add quirks** if needed in `config/quirks/providers.yml`
4. **Test**: `python -m giskit.indexer check-all --provider your-provider`
5. **Share**: Commit config file to git

## Schema Validation

Configs are validated against JSON schemas:

```bash
# Validate all configs
python -m giskit.config validate

# Validate specific file
python -m giskit.config validate config/services/pdok.yml
```

## Migration from Hardcoded

See `MIGRATION.md` for converting Python dicts to YAML configs.

## Examples

- **`config/services/pdok.yml`** - Full PDOK catalog (48 services)
- **`config/services/example.yml`** - Template for new providers
- **`config/quirks/formats.yml`** - CityJSON, GeoJSON quirks
- **`config/quirks/protocols.yml`** - OGC, WFS quirks

## Benefits for Users

1. **Add your own services** without touching code
2. **Version control** your service catalog
3. **Share configs** with team/community
4. **Validate** before deploying
5. **Monitor custom services** with same tools

## Future: Service Marketplace

```bash
# Install community configs
giskit config install github:user/my-services

# Publish your configs
giskit config publish my-services.yml
```
