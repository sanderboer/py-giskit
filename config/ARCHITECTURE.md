# GISKit Config-Driven Architecture

Dit document beschrijft de **config-driven** refactoring van giskit.

## Huidige Situatie (November 2025)

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
