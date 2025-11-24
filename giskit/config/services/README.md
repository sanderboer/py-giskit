# Legacy Services Directory

**⚠️ DEPRECATED:** This directory is deprecated as of v0.2.0.

## Migration Status

All service configurations have been migrated to the new provider-based structure:

- **Old location:** `giskit/config/services/pdok.yml`
- **New location:** `giskit/config/providers/pdok/ogc-features.yml`

## New Structure

The new config system uses a provider-centric structure:

```
giskit/config/providers/
├── pdok/
│   ├── provider.yml         # Provider metadata
│   ├── ogc-features.yml     # OGC API Features services
│   ├── wcs.yml              # Web Coverage Service
│   └── wmts.yml             # Web Map Tile Service
└── bag3d/
    ├── provider.yml
    └── ogc-features.yml
```

## Benefits of New Structure

1. **Auto-discovery:** Providers are automatically discovered and registered
2. **Protocol separation:** Each protocol gets its own config file
3. **Provider metadata:** Centralized provider information (homepage, license, etc.)
4. **Multiple protocols:** One provider can support multiple protocols cleanly
5. **Extensibility:** Easy to add new providers without code changes

## Migration Guide

If you have custom service configs in this directory:

### Step 1: Create provider directory
```bash
mkdir -p giskit/config/providers/my-provider
```

### Step 2: Create provider metadata
`giskit/config/providers/my-provider/provider.yml`:
```yaml
name: my-provider
title: My Data Provider
country: XX
homepage: https://example.com
license: CC0-1.0
defaults: {}
```

### Step 3: Create protocol config
`giskit/config/providers/my-provider/ogc-features.yml`:
```yaml
protocol: ogc-features

provider:
  name: my-provider
  title: My Data Provider
  # ... same metadata as provider.yml

services:
  my-service:
    url: https://api.example.com
    title: My Service
    category: my_category
    description: Service description
    keywords:
      - keyword1
      - keyword2
```

### Step 4: Test
```python
from giskit.providers.base import get_provider

# Your provider will be auto-discovered!
provider = get_provider("my-provider")
services = provider.get_supported_services()
print(services)  # ['my-service']
```

## Timeline

- **v0.2.0:** New provider system introduced, legacy configs deprecated
- **v0.4.0:** Legacy config loading support will be removed
- **v1.0.0:** This directory will be deleted

## Keeping Legacy Configs

These legacy files are kept temporarily for:
- Backward compatibility testing
- Reference during migration
- Emergency fallback

Do not add new services here - use the `providers/` directory instead.
