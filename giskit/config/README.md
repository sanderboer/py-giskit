# GISKit Configuration System

**Config-driven architecture** - All providers, services, and quirks defined in YAML.

## Directory Structure

```
giskit/config/
├── providers/              # Provider definitions (auto-discovered)
│   ├── pdok/              # Organization-specific configs
│   │   ├── provider.yml   # Provider metadata
│   │   ├── ogc-features.yml  # OGC API Features services
│   │   ├── wcs.yml        # WCS coverage services
│   │   ├── wmts.yml       # WMTS tile services
│   │   └── quirks.yml     # Provider-specific quirks
│   ├── bag3d/
│   │   ├── provider.yml
│   │   └── ogc-features.yml
│   └── custom/            # User-customizable providers
│
├── quirks/                # Protocol quirks
│   ├── protocols.yml      # Protocol-level quirks
│   └── formats.yml        # Format-specific quirks
│
└── export/                # Export configuration
    ├── colors.yml
    └── layer_mappings.yml
```

## Provider Auto-Discovery

Providers are automatically registered based on config files:

1. **Scan** `config/providers/{name}/` directories
2. **Detect** protocol files: `ogc-features.yml`, `wcs.yml`, `wmts.yml`
3. **Register** as: `"{name}"`, `"{name}-wcs"`, `"{name}-wmts"`

### Example:

```
config/providers/pdok/
  ├── provider.yml         # Metadata
  ├── ogc-features.yml     # → registers "pdok"
  ├── wcs.yml              # → registers "pdok-wcs"
  └── wmts.yml             # → registers "pdok-wmts"
```

## Config File Format

### provider.yml
```yaml
name: pdok
title: PDOK - Publieke Dienstverlening Op de Kaart
country: NL
homepage: https://www.pdok.nl
license: CC0-1.0
description: Dutch national spatial data infrastructure
```

### ogc-features.yml
```yaml
protocol: ogc-features
base_url_pattern: https://api.pdok.nl/{service}/ogc/v1/

services:
  bgt:
    url: https://api.pdok.nl/lv/bgt/ogc/v1_0/
    title: Basisregistratie Grootschalige Topografie
    category: base_registers
    collections:
      - pand
      - wegdeel
      - waterdeel
```

### wcs.yml
```yaml
protocol: wcs

services:
  ahn:
    url: https://service.pdok.nl/rws/ahn/wcs/v1_0
    title: Actueel Hoogtebestand Nederland
    category: elevation
    coverages:
      dsm: dsm_05m
      dtm: dtm_05m
```

## Migration from Legacy

Old hardcoded providers → New config-driven:

| Old | New |
|-----|-----|
| `PDOKProvider` class | `config/providers/pdok/` |
| `PDOK_SERVICES` dict | `ogc-features.yml` |
| Hardcoded quirks | `quirks.yml` |

## Benefits

✅ **No code changes** to add services
✅ **Version control** for service catalogs
✅ **User extensible** - add custom providers
✅ **Portable** - configs can be external
✅ **Validatable** - schema validation before use
