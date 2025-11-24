# Klimaateffectatlas Data Integration - Analyse

**Bron:** https://www.klimaateffectatlas.nl/
**WMS Service:** https://cas.cloud.sogelink.com/public/data/org/gws/YWFMLMWERURF/kea_public/wms
**Datum:** 24 november 2025
**Totaal aantal lagen:** ~287 WMS layers

---

## Executive Summary

De Klimaateffectatlas biedt **287 kaartlagen** via een WMS service met klimaatdata voor heel Nederland. De data is beschikbaar onder CC BY 4.0 licentie (bronvermelding verplicht). Integratie in GISKit is **zeer goed mogelijk** via WMS protocol.

### Integratiecomplexiteit: 🟢 LOW-MEDIUM
- **Protocol:** WMS (Web Map Service) - al ondersteund in GISKit
- **Dekking:** Heel Nederland
- **Resolutie:** Varieert per layer (100m-10m grid, buurt/gemeente aggregaties)
- **Licentie:** CC BY 4.0 (vrij te gebruiken met bronvermelding)
- **API Key:** Niet nodig
- **Kosten:** Gratis

---

## Hoofdcategorieën Klimaatdata

### 1. **HITTE & TEMPERATUUR** (~30 lagen)

#### Hitte-eilanden & Gevoelstemperatuur
- `hitteeiland` - Urban heat island effect
- `gevoelstemperatuur_2012` - Actuele gevoelstemperatuur
- `gevoelstemperatuur_2022` - Recente gevoelstemperatuur
- `GevoelstemperatuurBuurt_2012/2022` - Per buurt geaggregeerd

#### Extreme Temperaturen (huidig + 2050 projecties)
- `tropischedagen_huidig` / `tropischedagen_2050` - Dagen >30°C
- `warmedagen_huidig` / `warmedagen_2050` - Dagen >25°C
- `warme_nachten_huidig` / `warme_nachten_2050` - Tropische nachten
- `ijsdagen_huidig` / `ijsdagen_2050` - Dagen <0°C
- `vorstdagen_huidig` / `vorstdagen_2050` - Vorstperiodes

#### Hittestress & Kwetsbaarheid
- `sociale_kwetsbaarheid_hitte` - Kwetsbare groepen (ouderen, lage SES)
- `eenzame_75plussers_hitte` - Ouderen zonder sociaal netwerk
- `opwarming_oppervlaktewater_huidig/2050` - Watertemperatuur stijging

#### Koelte & Verlichting
- `Afstand_tot_koelte` - Nabijheid koele plekken (parken, water)

---

### 2. **WATEROVERLAST & NEERSLAG** (~50 lagen)

#### Extreme Neerslag (15mm & 25mm buien)
- `dagen_15mm_huidig` / `dagen_15mm_2050hoog/laag` - Frequentie zware buien
- `dagen_25mm_huidig` / `dagen_25mm_2050hoog/laag` - Extreme buien
- `neerslag_jaar_huidig` / `neerslag_jaar_2050` - Totale jaarlijkse neerslag

#### Grondwateroverlast
- `kans_grondwateroverlast_wateroverlast` - Kans op hoog grondwater
- `kans_grondwateroverlast_2050hoog` - Toekomstige risico's
- `kwel_infiltratie_huidig/2050` - Grondwaterstromen
- `Maatgevende_Grondwaterstand_GHG_1911_2010` - Historische grondwaterstanden
- `Maximale_Grondwaterstand_HG3_1911_2010` - Piekstanden

#### Wateroverlast & Erosie
- `gevoeligheid_watererosie` - Erosiegevoeligheid bodem
- `stedelijke_wateroverlast_2050/huidig` - Wateroverlast in bebouwd gebied

---

### 3. **OVERSTROMINGEN** (~80 lagen - regionaal)

#### Overstromingsscenario's (per risicoklasse)
- `maximale_waterdiepte_nederland_extreem_kleine_kans` - 1/10.000 jaar
- `maximale_waterdiepte_nederland_zeer_kleine_kans` - 1/1.000 jaar
- `maximale_waterdiepte_nederland_kleine_kans` - 1/100 jaar
- `maximale_waterdiepte_nederland_middelgrote_kans` - 1/10 jaar
- `maximale_waterdiepte_nederland_grote_kans` - Jaarlijks

#### Regionale Overstromingskaarten (BRS - Basisrisicobestand)
- Per waterschap (Achterhoek, Brabantse Delta, Rijnland, etc.)
- Waterdiepte bij dijkdoorbraak
- Overstromingsduur
- Stroomsnelheden

#### Droge Plekken & Evacuatie
- `Droge_plekken_Extreem_kleine_kans` - Veilige hoogtes bij overstroming
- `droge_verdiepingen_extreem_kleine_kans` - Verdiepingen boven water

---

### 4. **DROOGTE** (~15 lagen)

#### Droogtestress (vegetatie & landbouw)
- `droogtestress_huidig` / `droogtestress_2050` - Droogtegevoeligheid
- `droogtegevoeligheidgrondwaterafhankelijkenatuur` - Kwetsbare natuur
- `ligging_grensvlak_tussen_zoet_en_zout_grondwater` - Verzilting risico

---

### 5. **GROEN, GRIJS & WATER** (~20 lagen)

#### Landgebruik per Buurt
- `boom_per_buurt` - Boomdichtheid
- `groen_per_buurt` - Percentage groen
- `grijs_per_buurt` - Percentage verharding
- `water_per_buurt` - Percentage water

#### Schaduw & Koelte
- `buurten_schaduwkaart_fiets_en_wandelpaden` - Schaduw op routes

---

### 6. **BODEMDALING** (~10 lagen)

#### Projecties
- `bodemdaling_2020_2050hoog/laag` - Scenario's tot 2050
- `bodemdaling_2020_2100hoog/laag` - Scenario's tot 2100
- `bodemdaling_ophoging` - Benodigde ophoging

---

### 7. **ZEESPIEGELSTIJGING** (~15 lagen)

#### Kustlijnen & Getijzones
- `kustlijn_2100` / `kustlijn_2150` / `kustlijn_2200` - Projecties
- `laagwaterlijn` / `hoogwaterlijn` - Getijzones
- `Zeespiegelstijging_2100_Hoog` / `Laag` - Verschillende scenario's

---

### 8. **SOCIALE KWETSBAARHEID** (~15 lagen)

#### Demografische Kwetsbaarheid
- `sociale_kwetsbaarheid_hitte` - Kwetsbare groepen hitte
- `eenzame_75plussers_hitte` - Ouderen zonder netwerk
- `kwetsbare_groepen_wateroverlast` - Kwetsbaar voor overstromingen

---

### 9. **KLIMAATSCENARIO'S (KNMI)** (~20 lagen)

#### Temperatuur, Neerslag, Zeespiegel
- Verschillende KNMI-scenario's (GL, GH, WL, WH)
- Tijdshorizonnen: 2050, 2085, 2100, 2150, 2200

---

## Prioriteit voor GISKit Integratie

### 🔴 **HIGH PRIORITY** - Meest gevraagd voor woningbouw/projectontwikkeling

| Laag | Use Case | Impact |
|------|----------|--------|
| `hitteeiland` | Hitte-eiland effect stedelijk gebied | ⭐⭐⭐ |
| `maximale_waterdiepte_*_kleine_kans` | Overstromingsrisico | ⭐⭐⭐ |
| `kans_grondwateroverlast` | Grondwaterproblemen | ⭐⭐⭐ |
| `dagen_15mm_2050hoog` | Extreme neerslag frequentie | ⭐⭐⭐ |
| `groen_per_buurt` | Groenvoorziening | ⭐⭐⭐ |
| `sociale_kwetsbaarheid_hitte` | Kwetsbare groepen | ⭐⭐ |
| `bodemdaling_2020_2050` | Funderingsproblemen | ⭐⭐⭐ |

### 🟡 **MEDIUM PRIORITY** - Specifieke analyses

| Laag | Use Case |
|------|----------|
| `tropischedagen_2050` | Klimaatadaptatie woningen |
| `droogtestress_2050` | Groenbeleid |
| `gevoelstemperatuur_buurt` | Leefbaarheid |
| `Afstand_tot_koelte` | Parkplanning |

### 🟢 **LOW PRIORITY** - Specialistische toepassingen

- Regionale overstromingsmodellen (BRS per waterschap)
- Extreme zeespiegelstijging (2200)
- Erosiegevoeligheid

---

## Technische Integratie in GISKit

### Optie 1: WMS Protocol (Raster) - **AANBEVOLEN**

**Voor:** Heatmaps, overstromingskaarten, klimaatprojecties

```yaml
# giskit/config/providers/klimaateffectatlas.yml
provider:
  name: "klimaateffectatlas"
  title: "Klimaateffectatlas Nederland"
  url: "https://cas.cloud.sogelink.com/public/data/org/gws/YWFMLMWERURF/kea_public/wms"
  attribution: "Klimaateffectatlas, 2025"
  license: "CC BY 4.0"

services:
  hitte-eiland:
    id: "hitteeiland"
    title: "Hitte-eiland Effect"
    protocol: "wms"
    layer: "hitteeiland"
    category: "climate"

  overstroming-klein:
    id: "overstroming-kleine-kans"
    title: "Overstromingsrisico (1/100 jaar)"
    protocol: "wms"
    layer: "maximale_waterdiepte_nederland_kleine_kans_20251120"
    category: "climate"

  grondwater-overlast:
    id: "grondwateroverlast"
    title: "Kans op Grondwateroverlast"
    protocol: "wms"
    layer: "kans_grondwateroverlast_wateroverlast"
    category: "climate"
```

**Voordelen:**
- Alle 287 lagen direct beschikbaar
- Geen geocoding nodig
- Raster data (grid-based) - perfecte resolutie
- WMS protocol al ondersteund in GISKit

**Nadelen:**
- Raster data (niet vector) - lastig voor analyses
- Geen attributen per object
- Pixel-based queries

---

### Optie 2: Download GIS Data + PostGIS (Vector)

**Voor:** Analyses, statistieken, combinaties met andere data

Via de [data opvraag pagina](https://www.klimaateffectatlas.nl/nl/data-opvragen):
- Download ShapeFile/GeoPackage
- Laad in PostGIS database
- Serveer via OGC API Features

**Voordelen:**
- Vector data - volledige analyses mogelijk
- Attributen beschikbaar
- Combineerbaar met BGT/BAG/AHN

**Nadelen:**
- Handmatige download per laag
- Database setup nodig
- Meer complexe architectuur

---

## Aanbeveling voor GISKit

### **Fase 1: WMS Integratie (1-2 dagen)**

Integreer top 10 meest gevraagde lagen via WMS:

1. ✅ `hitteeiland` - Hitte-eiland
2. ✅ `maximale_waterdiepte_nederland_kleine_kans` - Overstroming 1/100jr
3. ✅ `kans_grondwateroverlast_wateroverlast` - Grondwater
4. ✅ `dagen_15mm_2050hoog` - Extreme neerslag 2050
5. ✅ `groen_per_buurt` - Groenvoorziening
6. ✅ `sociale_kwetsbaarheid_hitte` - Kwetsbare groepen
7. ✅ `bodemdaling_2020_2050hoog` - Bodemdaling
8. ✅ `tropischedagen_2050_hitte` - Tropische dagen 2050
9. ✅ `gevoelstemperatuur_2022` - Gevoelstemperatuur
10. ✅ `Afstand_tot_koelte` - Afstand tot koelte

### **Fase 2: Uitbreiding op aanvraag**

Voeg extra lagen toe op basis van user feedback.

---

## Use Cases voor Woningbouw/Projectontwikkeling

### 1. **Klimaatadaptatie Scan Nieuwbouwlocatie**
```python
# Haal alle klimaatrisico's op voor een locatie
from giskit.catalog import get_provider

kea = get_provider('klimaateffectatlas')

# Recipe: Klimaat check Curieweg Amsterdam
datasets = [
    'hitteeiland',              # Hitte-eiland effect
    'kans_grondwateroverlast',  # Grondwater problemen
    'maximale_waterdiepte_kleine_kans',  # Overstromingsrisico
    'dagen_15mm_2050hoog',      # Toekomstige extreme buien
]
```

**Output:** Heatmaps + risico-indicatoren voor klimaatadaptatie

### 2. **Sociale Klimaatkwetsbaarheid Analyse**
```python
# Combineer klimaatrisico's met sociale kwetsbaarheid
datasets = [
    'sociale_kwetsbaarheid_hitte',  # Kwetsbare groepen
    'groen_per_buurt',              # Groenvoorziening
    'Afstand_tot_koelte',           # Koele plekken
    'eenzame_75plussers_hitte',     # Ouderen
]
```

**Output:** Prioriteitskaart voor groenvoorzieningen

### 3. **Toekomstige Wateroverlast (2050)**
```python
datasets = [
    'dagen_15mm_2050hoog',          # Extreme buien
    'kans_grondwateroverlast_2050hoog',  # Grondwater
    'bodemdaling_2020_2050hoog',    # Bodemdaling
]
```

**Output:** Risicoprofiel voor drainage/funderingen

---

## Bronvermelding

**Verplicht bij gebruik:**
```
"Klimaateffectatlas, 2025"
```

Licentie: CC BY 4.0 - https://creativecommons.org/licenses/by/4.0/

---

## Volgende Stappen

1. ✅ Implementeer WMS protocol support in GISKit (al aanwezig)
2. 🔲 Maak Klimaateffectatlas provider config (30 min)
3. 🔲 Selecteer top 10 lagen voor initiële integratie (1 uur)
4. 🔲 Test WMS queries met bbox (1 uur)
5. 🔲 Maak voorbeeldrecipe "Klimaat Check Nieuwbouwlocatie" (30 min)
6. 🔲 Documenteer in catalog (30 min)

**Totaal:** ~4 uur voor volledige integratie van 10 belangrijkste klimaatlagen!

---

## Contactgegevens

- **Website:** https://www.klimaateffectatlas.nl
- **Helpdesk:** Via website formulier
- **Data opvragen:** https://www.klimaateffectatlas.nl/nl/data-opvragen
- **Metadata:** [Excel sheet](https://www.klimaateffectatlas.nl/l/nl/library/download/urn:uuid:6ffa57ad-5aa5-4958-941d-dd8c72664af9/metadataklimaateffectatlas.xlsx)
