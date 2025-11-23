# PDOK Service Index Monitor

Tool om de PDOK service index te onderhouden en monitoren.

## Features

✅ **Health Checking** - Test of alle 40+ PDOK services nog werken
✅ **Deprecation Detection** - Detecteer services die niet meer bestaan (404)
✅ **Service Discovery** - Vind nieuwe PDOK services automatisch
✅ **Performance Monitoring** - Meet response times per service
✅ **Collection Counting** - Tel hoeveel layers elk service heeft
✅ **Version Detection** - Detecteer API versie upgrades (v1 → v2)

## Gebruik

### Check alle services

```bash
python -m giskit.indexer check-all
```

Output:
```
Checking 48 PDOK services...
  Checking bgt... ✓ OK (49 collections)
  Checking bag... ✓ OK (0 collections)
  Checking brk... ✗ NOT FOUND - may be deprecated!
  ...

HEALTH CHECK COMPLETE
Healthy:   47
Unhealthy: 1
```

### Check specifieke service

```bash
python -m giskit.indexer check bgt
```

Output:
```
Service: bgt
Status:  healthy
Collections: 49
Response time: 0.06s
```

### Discover nieuwe services

```bash
python -m giskit.indexer discover
```

Scant PDOK API endpoints voor nieuwe services die nog niet in de index zitten.

### Genereer volledige report

```bash
python -m giskit.indexer report
```

Of save naar bestand:
```bash
python -m giskit.indexer report --output pdok_health_report.txt
```

## Onderhoud Workflow

### Maandelijkse check (aanbevolen)

```bash
# 1. Check health van alle services
python -m giskit.indexer check-all

# 2. Als er issues zijn, genereer report
python -m giskit.indexer report --output report_$(date +%Y%m%d).txt

# 3. Discover nieuwe services
python -m giskit.indexer discover
```

### Bij deprecated services

Als een service `NOT FOUND` (404) is:

1. **Check PDOK.nl** - Is de service verplaatst of vervangen?
2. **Update URL** - Pas de URL aan in `pdok.py` als service verhuisd is
3. **Verwijder** - Verwijder uit `PDOK_SERVICES` als echt deprecated
4. **Update docs** - Update `PDOK_SERVICES.md` met wijzigingen

### Bij nieuwe services

Als `discover` nieuwe services vindt:

1. **Verifieer** - Check of het relevante services zijn
2. **Metadata toevoegen** - Voeg toe aan `PDOK_SERVICES` in `pdok.py`:
   ```python
   "nieuwe-service": {
       "url": "https://api.pdok.nl/...",
       "title": "Service Naam",
       "category": "base_registers",  # of andere categorie
       "description": "Beschrijving van de service",
       "keywords": ["keyword1", "keyword2"],
   }
   ```
3. **Test** - Run `python -m giskit.indexer check nieuwe-service`
4. **Update docs** - Voeg toe aan `PDOK_SERVICES.md`

## Timeout aanpassen

Sommige services zijn traag (vooral 3D services). Pas timeout aan:

```bash
python -m giskit.indexer check-all --timeout 30.0
```

## Programmatisch gebruik

```python
from giskit.indexer import check_service_health, PDOKServiceMonitor

# Check één service
result = check_service_health("bgt")
print(f"Status: {result['status']}")
print(f"Collections: {result['collections_found']}")

# Check alle services
monitor = PDOKServiceMonitor()
results = monitor.check_all_services()

print(f"Healthy: {len(results['healthy'])}")
print(f"Unhealthy: {len(results['unhealthy'])}")

# Generate report
report = monitor.generate_report()
print(report)
```

## Automatisering met cron

Check wekelijks op maandag 9:00:

```cron
0 9 * * 1 cd /path/to/giskit && python -m giskit.indexer report --output /tmp/pdok_report.txt && mail -s "PDOK Health Report" you@example.com < /tmp/pdok_report.txt
```

## Exit Codes

- `0` - Alle services healthy
- `1` - Één of meer services unhealthy, of nieuwe services discovered
- `130` - Interrupted by user (Ctrl+C)

Gebruik in CI/CD:

```bash
#!/bin/bash
python -m giskit.indexer check-all
if [ $? -ne 0 ]; then
    echo "⚠️ PDOK services have issues!"
    python -m giskit.indexer report
    exit 1
fi
```

## Troubleshooting

### Service timeout

```bash
# Verhoog timeout voor trage services
python -m giskit.indexer check bag3d --timeout 60.0
```

### Connection errors

```bash
# Check internet connectie
ping api.pdok.nl

# Check of PDOK bereikbaar is
curl -I https://api.pdok.nl
```

### Discovery vindt niks

Discovery is basic HTML scraping. Als PDOK hun website structuur verandert, kan discovery stoppen met werken. Niet erg - we hebben al 48 services in de index!

## Bekende Issues

### BRK Service (404)

De BRK service (`brk`) geeft momenteel 404. Dit is een bekend issue:
- **Status**: Deprecated of verplaatst
- **Actie**: Check https://www.pdok.nl voor updates

### 3D Services (Timeout)

3D services (bag3d, 3d-basisvoorziening) kunnen traag zijn:
- **Oplossing**: Gebruik `--timeout 30` of hoger
- **Reden**: CityJSON data is zwaar

## Links

- **PDOK Homepage**: https://www.pdok.nl
- **PDOK API Docs**: https://api.pdok.nl
- **Service Catalog**: `PDOK_SERVICES.md`
