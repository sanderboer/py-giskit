# GISKit IFC Export Implementation Plan

**Goal**: Add config-driven IFC export to GISKit, following the same spirit as the recipe system for downloads.

**Date**: November 23, 2024  
**Status**: Planning Phase

---

## Executive Summary

Implement IFC export for GeoPackage data with:
- **Config-driven approach** using YAML for layer mappings and colors
- **Export recipes** defining what layers to export and how
- **Modular exporter plugins** for different layer types
- **Material/color system** from Sitedb adapted to YAML config
- **CLI integration** with `giskit export ifc` command

**Key Principle**: Same config-driven philosophy as download recipes, but for IFC export.

---

## 1. Architecture Overview

### 1.1 Current Sitedb Architecture (Reference)

```
Sitedb IFC Export:
├── ifc_exporter.py          # Main orchestrator
├── layer_exporters.py       # Plugin system (BgtPandExporter, BgtWegdeelExporter, etc.)
├── layer_config.py          # Hard-coded LayerConfig dataclasses
├── materials.py             # Hard-coded BGT_COLORS and BGT_MATERIALS dicts
├── ifc_geometry.py          # Geometry conversion utilities
└── schema_adapter.py        # IFC version abstraction (IFC4 vs IFC4X3)
```

**Strengths**:
- ✅ Plugin system with `LayerExporter` ABC
- ✅ Clean separation: exporter → geometry → materials
- ✅ Schema adapter handles IFC version differences

**Limitations**:
- ❌ Hard-coded color dicts in Python
- ❌ Hard-coded layer configs (dataclasses)
- ❌ No recipe system for export workflow
- ❌ No user-customizable colors without code changes

### 1.2 Proposed GISKit Architecture

```
giskit/
├── giskit/
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base exporter ABC
│   │   ├── ifc/
│   │   │   ├── __init__.py
│   │   │   ├── exporter.py            # Main IFC exporter
│   │   │   ├── layer_exporters.py     # Layer-specific exporters
│   │   │   ├── geometry.py            # Geometry conversion
│   │   │   ├── materials.py           # Material/color management
│   │   │   └── schema_adapter.py      # IFC version handling
│   │   └── recipe.py                  # Export recipe model
│   │
│   ├── config/
│   │   ├── export/
│   │   │   ├── layer_mappings.yml     # Layer → IFC entity mappings
│   │   │   ├── colors.yml             # Layer color definitions
│   │   │   └── materials.yml          # Material definitions
│   │
│   ├── cli/
│   │   └── main.py                    # Add "export" command group
│   │
├── export_recipes/
│   ├── README.md
│   ├── complete_site.json             # Full export with all layers
│   ├── onderlegger_only.json          # Exclude buildings
│   ├── buildings_only.json            # Only buildings (BAG3D + BAG)
│   └── custom_colors.json             # Example with custom color overrides
│
└── examples/
    └── export_to_ifc.sh               # Example bash script
```

---

## 2. Implementation Plan

### Phase 1: Core Infrastructure ⭐ (Week 1)

**1.1 Export Recipe Model** (`giskit/exporters/recipe.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ExportRecipe(BaseModel):
    """Recipe for exporting GeoPackage to IFC."""
    
    name: str
    description: Optional[str] = None
    
    # Input
    input_path: str = Field(..., description="Path to GeoPackage file")
    
    # Output
    output_path: str = Field(..., description="Output IFC file path")
    ifc_version: str = Field("IFC4X3_ADD2", description="IFC schema version")
    
    # Layer selection
    layers: Optional[List[str]] = Field(None, description="Layers to export (None = all)")
    exclude_layers: Optional[List[str]] = Field(None, description="Layers to exclude")
    
    # Coordinate handling
    relative_coords: bool = Field(True, description="Use relative coordinates")
    normalize_z: bool = Field(True, description="Normalize Z to ground level")
    
    # Material/color overrides
    color_overrides: Optional[Dict[str, Dict[str, tuple[float, float, float]]]] = None
    material_overrides: Optional[Dict[str, str]] = None
    
    # Metadata
    author: str = Field("GISKit", description="IFC author")
    organization: str = Field("", description="Organization name")
    
    @classmethod
    def from_file(cls, path: str) -> "ExportRecipe":
        """Load recipe from JSON file."""
        import json
        with open(path) as f:
            return cls(**json.load(f))
```

**1.2 Config Loader for Export Configs** (`giskit/config/loader.py` - extend)

Add functions:
- `load_layer_mappings()` - Load layer → IFC mappings from YAML
- `load_color_config()` - Load color definitions
- `load_material_config()` - Load material definitions

**1.3 Base Exporter ABC** (`giskit/exporters/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class Exporter(ABC):
    """Base class for all exporters."""
    
    @abstractmethod
    def export(
        self,
        input_path: str,
        output_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Export data to target format.
        
        Returns:
            Statistics dict
        """
        pass
```

---

### Phase 2: YAML Configuration Files ⭐ (Week 1)

**2.1 Layer Mappings** (`giskit/config/export/layer_mappings.yml`)

```yaml
# Layer → IFC entity mappings
layer_mappings:
  bgt_pand:
    ifc_class: IfcBuilding
    assignment_method: aggregate
    default_height: 8.0
    name_attribute: bag_pand_id
    pset_name: Pset_BGT
    properties:
      - gml_id
      - lokaal_id
      - bag_pand_id
      - bgt_status
      - bronhouder
    color_attributes:
      - plus_fysiek_voorkomen
      - functie
  
  bgt_wegdeel:
    ifc_class: IfcRoad  # IFC4X3
    ifc_class_fallback: IfcCivilElement  # IFC4
    assignment_method: aggregate
    default_height: 0.3
    name_attribute: lokaal_id
    pset_name: Pset_BGT_Wegdeel
    properties:
      - gml_id
      - lokaal_id
      - functie
      - plus_fysiek_voorkomen
    color_attributes:
      - plus_fysiek_voorkomen
      - functie
  
  bgt_waterdeel:
    ifc_class: IfcGeographicElement
    assignment_method: spatial
    default_height: 0.1
    name_attribute: lokaal_id
    pset_name: Pset_BGT_Waterdeel
    properties:
      - gml_id
      - lokaal_id
      - type
      - plus_type
    color_attributes:
      - type
      - plus_type
  
  bgt_begroeidterreindeel:
    ifc_class: IfcGeographicElement
    assignment_method: spatial
    default_height: 0.05
    name_attribute: lokaal_id
    pset_name: Pset_BGT_Begroeid
    properties:
      - gml_id
      - lokaal_id
      - fysiek_voorkomen
      - plus_fysiek_voorkomen
    color_attributes:
      - plus_fysiek_voorkomen
      - fysiek_voorkomen
  
  bgt_onbegroeidterreindeel:
    ifc_class: IfcGeographicElement
    assignment_method: spatial
    default_height: 0.02
    name_attribute: lokaal_id
    pset_name: Pset_BGT_Onbegroeid
    properties:
      - gml_id
      - lokaal_id
      - fysiek_voorkomen
      - plus_fysiek_voorkomen
    color_attributes:
      - fysiek_voorkomen
      - plus_fysiek_voorkomen
  
  bgt_ondersteunendwegdeel:
    ifc_class: IfcCivilElement
    assignment_method: spatial
    default_height: 0.2
    name_attribute: lokaal_id
    pset_name: Pset_BGT_OndersteunendWegdeel
    properties:
      - gml_id
      - lokaal_id
      - functie
      - plus_fysiek_voorkomen
    color_attributes:
      - functie
      - plus_fysiek_voorkomen
  
  bag3d_lod22:
    ifc_class: IfcBuilding
    assignment_method: aggregate
    default_height: 0.0  # Uses 3D geometry
    name_attribute: identificatie
    pset_name: Pset_BAG3D
    properties:
      - identificatie
      - bouwjaar
      - status
      - h_dak_max
      - h_dak_min
      - h_maaiveld
      - opp_grond
      - dak_type
    surface_classification: true  # Enable roof/wall detection
  
  bag_pand:
    ifc_class: IfcBuilding
    assignment_method: aggregate
    default_height: 8.0
    name_attribute: identificatie
    pset_name: Pset_BAG_Pand
    properties:
      - identificatie
  
  brk_perceel:
    ifc_class: IfcGeographicElement
    assignment_method: spatial
    default_height: 0.02
    name_attribute: identificatie
    pset_name: Pset_BRK_Perceel
    properties:
      - identificatie
      - kadastralegemeente
      - sectie
      - perceelnummer
      - oppervlakte
```

**2.2 Color Definitions** (`giskit/config/export/colors.yml`)

```yaml
# RGB colors (0-1 range) for Dutch infrastructure
# Organized by layer and attribute values

bgt_pand:
  default: [0.85, 0.85, 0.85]  # Light gray

bgt_wegdeel:
  # By functie
  rijbaan: [0.3, 0.3, 0.3]  # Dark gray (asphalt)
  "rijbaan lokale weg": [0.3, 0.3, 0.3]
  fietspad: [0.3, 0.3, 0.3]
  voetpad: [0.3, 0.3, 0.3]
  "voetpad op trap": [0.3, 0.3, 0.3]
  inrit: [0.3, 0.3, 0.3]
  woonerf: [0.3, 0.3, 0.3]
  
  # By fysiek_voorkomen (surface material)
  asfalt: [0.3, 0.3, 0.3]
  tegels: [0.65, 0.65, 0.65]  # Light gray tiles
  betonstraatstenen: [0.6, 0.6, 0.6]
  "gebakken klinkers": [0.7, 0.3, 0.25]  # Red brick
  "beton element": [0.55, 0.55, 0.55]
  
  default: [0.4, 0.4, 0.4]  # Medium gray

bgt_waterdeel:
  sloot: [0.15, 0.35, 0.65]  # Dark blue (ditch)
  vijver: [0.2, 0.45, 0.75]  # Medium blue (pond)
  waterloop: [0.18, 0.4, 0.7]  # Blue (stream)
  default: [0.2, 0.4, 0.7]  # Blue

bgt_begroeidterreindeel:
  "gras- en kruidachtigen": [0.3, 0.6, 0.3]  # Green
  groenvoorziening: [0.35, 0.65, 0.35]
  heesters: [0.25, 0.5, 0.25]  # Darker green
  bosplantsoen: [0.15, 0.4, 0.15]  # Dark green
  planten: [0.35, 0.65, 0.35]
  bodembedekkers: [0.28, 0.55, 0.28]
  default: [0.4, 0.6, 0.3]

bgt_onbegroeidterreindeel:
  erf: [0.75, 0.65, 0.55]  # Light brown
  "gesloten verharding": [0.5, 0.5, 0.5]
  "open verharding": [0.65, 0.6, 0.55]
  onverhard: [0.7, 0.6, 0.5]
  zand: [0.85, 0.75, 0.6]
  default: [0.7, 0.6, 0.5]

bgt_ondersteunendwegdeel:
  berm: [0.4, 0.55, 0.35]  # Greenish
  verkeerseiland: [0.45, 0.45, 0.45]
  default: [0.5, 0.5, 0.5]

bag3d:
  # Surface type-based colors
  roof: [0.6, 0.3, 0.2]  # Red/brown roof tiles
  wall: [0.85, 0.75, 0.65]  # Beige brick
  default: [0.8, 0.75, 0.7]

brk_perceel:
  default: [0.9, 0.9, 0.85]  # Very light beige (subtle)
```

**2.3 Material Definitions** (`giskit/config/export/materials.yml`)

```yaml
# Material names for IFC elements

bgt_wegdeel:
  rijbaan: Asphalt
  fietspad: Brick Pavement
  voetpad: Concrete Pavement
  asfalt: Asphalt
  tegels: Concrete Tiles
  "gebakken klinkers": Brick Pavers
  default: Road Surface

bgt_pand:
  default: Brick Masonry

bgt_waterdeel:
  default: Water

bgt_begroeidterreindeel:
  "gras- en kruidachtigen": Grass
  bosplantsoen: Forest Vegetation
  default: Vegetation

bag3d:
  roof: Roof Tiles
  wall: Brick Wall
  default: Building Material

brk_perceel:
  default: Cadastral Boundary
```

---

### Phase 3: IFC Exporter Implementation ⭐⭐ (Week 2)

**3.1 Main IFC Exporter** (`giskit/exporters/ifc/exporter.py`)

Port from Sitedb with modifications:
- Load config from YAML instead of hard-coded dicts
- Use `ExportRecipe` for configuration
- Integrate with GISKit's config system

**3.2 Layer Exporters** (`giskit/exporters/ifc/layer_exporters.py`)

Port from Sitedb:
- `LayerExporter` ABC
- `BgtPandExporter`
- `BgtWegdeelExporter`
- `BgtWaterdeelExporter`
- `BgtBegroeidExporter`
- `BgtOnbegroeidExporter`
- `Bag3dExporter` (with surface classification)
- `BagPandExporter`
- `BrkPerceelExporter`

Use config loader to get layer mappings instead of hard-coded.

**3.3 Materials System** (`giskit/exporters/ifc/materials.py`)

Port from Sitedb but load from YAML:
```python
from giskit.config.loader import load_color_config, load_material_config

class MaterialManager:
    """Manage IFC materials and colors from config."""
    
    def __init__(self):
        self.colors = load_color_config()
        self.materials = load_material_config()
    
    def get_color(self, layer_name: str, attribute_value: Optional[str] = None) -> tuple:
        """Get color from config."""
        # ... lookup in self.colors dict
    
    def get_material_name(self, layer_name: str, attribute_value: Optional[str] = None) -> str:
        """Get material name from config."""
        # ... lookup in self.materials dict
```

**3.4 Geometry Conversion** (`giskit/exporters/ifc/geometry.py`)

Port from Sitedb (no changes needed):
- `transform_to_relative()`
- `normalize_z_to_ground()`
- `create_extruded_area_solid()`
- `create_faceted_brep()`
- `polygon_3d_to_ifc_face()`
- `classify_surface()` (roof vs wall detection)

**3.5 Schema Adapter** (`giskit/exporters/ifc/schema_adapter.py`)

Port from Sitedb (no changes needed):
- Handle IFC4 vs IFC4X3 differences
- Fallback logic (IfcRoad → IfcCivilElement in IFC4)

---

### Phase 4: CLI Integration ⭐ (Week 2)

**4.1 Export Command Group** (`giskit/cli/main.py`)

```python
export_app = typer.Typer(help="Export data to various formats")
app.add_typer(export_app, name="export")

@export_app.command("ifc")
def export_ifc(
    input_path: Path = typer.Argument(..., help="Input GeoPackage path"),
    output_path: Path = typer.Argument(..., help="Output IFC path"),
    recipe: Optional[Path] = typer.Option(None, "--recipe", "-r", help="Export recipe JSON"),
    layers: Optional[str] = typer.Option(None, "--layers", help="Comma-separated layer names"),
    exclude: Optional[str] = typer.Option(None, "--exclude", help="Comma-separated layers to exclude"),
    ifc_version: str = typer.Option("IFC4X3_ADD2", "--version", help="IFC schema version"),
    relative: bool = typer.Option(True, "--relative/--absolute", help="Coordinate mode"),
    normalize_z: bool = typer.Option(True, "--normalize-z/--raw-z", help="Z normalization"),
):
    """Export GeoPackage to IFC format.
    
    Examples:
        # Export all layers
        giskit export ifc site.gpkg site.ifc
        
        # Export specific layers
        giskit export ifc site.gpkg site.ifc --layers bgt_wegdeel,bag3d_lod22
        
        # Export without buildings
        giskit export ifc site.gpkg onderlegger.ifc --exclude bag_pand,bag3d_lod22
        
        # Use export recipe
        giskit export ifc site.gpkg site.ifc --recipe export_recipes/complete_site.json
    """
    # ... implementation
```

---

### Phase 5: Export Recipes ⭐ (Week 2)

**5.1 Example Export Recipes** (`export_recipes/`)

**Complete Site Export** (`complete_site.json`):
```json
{
  "name": "Complete Site Export",
  "description": "Export all layers with default settings",
  "input_path": "site_underlegger.gpkg",
  "output_path": "site_complete.ifc",
  "ifc_version": "IFC4X3_ADD2",
  "relative_coords": true,
  "normalize_z": true,
  "author": "GISKit",
  "organization": "A190"
}
```

**Onderlegger Only** (`onderlegger_only.json`):
```json
{
  "name": "Onderlegger (Base Map) Export",
  "description": "Topography without buildings",
  "input_path": "site_underlegger.gpkg",
  "output_path": "onderlegger.ifc",
  "ifc_version": "IFC4X3_ADD2",
  "exclude_layers": [
    "bag_pand",
    "bgt_pand",
    "bag3d_lod12",
    "bag3d_lod13",
    "bag3d_lod22"
  ],
  "relative_coords": true,
  "normalize_z": true
}
```

**Buildings Only** (`buildings_only.json`):
```json
{
  "name": "Buildings Only Export",
  "description": "3D buildings (BAG3D LOD 2.2) only",
  "input_path": "site_underlegger.gpkg",
  "output_path": "buildings.ifc",
  "ifc_version": "IFC4X3_ADD2",
  "layers": [
    "bag3d_lod22"
  ],
  "relative_coords": true,
  "normalize_z": true
}
```

**Custom Colors** (`custom_colors.json`):
```json
{
  "name": "Custom Color Export",
  "description": "Override default colors for specific layers",
  "input_path": "site_underlegger.gpkg",
  "output_path": "site_custom_colors.ifc",
  "ifc_version": "IFC4X3_ADD2",
  "color_overrides": {
    "bgt_wegdeel": {
      "default": [0.2, 0.2, 0.2],
      "fietspad": [1.0, 0.0, 0.0]
    },
    "bag3d": {
      "roof": [0.8, 0.1, 0.1],
      "wall": [0.9, 0.9, 0.8]
    }
  },
  "relative_coords": true,
  "normalize_z": true
}
```

---

### Phase 6: Integration & Testing ⭐ (Week 3)

**6.1 Integration with Download Workflow**

Example combined workflow script (`examples/download_and_export.sh`):

```bash
#!/usr/bin/env bash
# Download site data and export to IFC

ADDRESS="$1"
RADIUS="${2:-500}"

echo "Step 1: Download site data"
cd giskit/examples
./build_site_underlegger.sh "$ADDRESS" "$RADIUS" site.gpkg

echo "Step 2: Export to IFC"
giskit export ifc site.gpkg site_complete.ifc

echo "Step 3: Export onderlegger (without buildings)"
giskit export ifc site.gpkg onderlegger.ifc --exclude bag_pand,bag3d_lod22,bgt_pand

echo "Done!"
echo "  - Complete IFC: site_complete.ifc"
echo "  - Onderlegger:  onderlegger.ifc"
```

**6.2 Unit Tests** (`giskit/tests/unit/test_ifc_export.py`)

- Test config loading (colors, materials, mappings)
- Test export recipe validation
- Test material manager
- Test geometry conversion utilities

**6.3 Integration Tests** (`giskit/tests/integration/test_ifc_export.py`)

- Test full export workflow with test GeoPackage
- Test different IFC versions (IFC4, IFC4X3)
- Test layer filtering
- Test color overrides
- Validate IFC output with IfcOpenShell

---

## 3. File Structure Summary

```
giskit/
├── giskit/
│   ├── exporters/
│   │   ├── __init__.py                         # NEW
│   │   ├── base.py                             # NEW - Base exporter ABC
│   │   ├── recipe.py                           # NEW - ExportRecipe model
│   │   └── ifc/
│   │       ├── __init__.py                     # NEW
│   │       ├── exporter.py                     # NEW - Main IFC exporter
│   │       ├── layer_exporters.py              # NEW - Layer-specific exporters
│   │       ├── geometry.py                     # NEW - Geometry conversion
│   │       ├── materials.py                    # NEW - Material/color manager
│   │       └── schema_adapter.py               # NEW - IFC version handling
│   │
│   ├── config/
│   │   ├── loader.py                           # MODIFY - Add export config loaders
│   │   └── export/
│   │       ├── layer_mappings.yml              # NEW - Layer → IFC mappings
│   │       ├── colors.yml                      # NEW - Color definitions
│   │       └── materials.yml                   # NEW - Material names
│   │
│   └── cli/
│       └── main.py                             # MODIFY - Add "export" command group
│
├── export_recipes/                             # NEW
│   ├── README.md
│   ├── complete_site.json
│   ├── onderlegger_only.json
│   ├── buildings_only.json
│   └── custom_colors.json
│
├── examples/
│   ├── download_and_export.sh                  # NEW - Combined workflow
│   └── ... (existing examples)
│
├── tests/
│   ├── unit/
│   │   └── test_ifc_export.py                  # NEW
│   └── integration/
│       └── test_ifc_export_integration.py      # NEW
│
└── pyproject.toml                              # MODIFY - Add ifcopenshell dependency
```

---

## 4. Dependencies

**Add to `pyproject.toml`**:

```toml
[tool.poetry.dependencies]
ifcopenshell = "^0.8.0"  # IFC toolkit

[tool.poetry.group.dev.dependencies]
# ... existing dev deps
```

---

## 5. Migration from Sitedb

### Files to Port

| Sitedb File | GISKit Location | Changes |
|-------------|-----------------|---------|
| `ifc_exporter.py` | `giskit/exporters/ifc/exporter.py` | Use config loader, ExportRecipe |
| `layer_exporters.py` | `giskit/exporters/ifc/layer_exporters.py` | Load mappings from YAML |
| `materials.py` | `giskit/exporters/ifc/materials.py` | Load colors/materials from YAML |
| `ifc_geometry.py` | `giskit/exporters/ifc/geometry.py` | No changes (utility functions) |
| `schema_adapter.py` | `giskit/exporters/ifc/schema_adapter.py` | No changes |
| `layer_config.py` | `config/export/layer_mappings.yml` | Convert to YAML |
| `BGT_COLORS` dict | `config/export/colors.yml` | Convert to YAML |
| `BGT_MATERIALS` dict | `config/export/materials.yml` | Convert to YAML |

---

## 6. Usage Examples

### Example 1: Basic Export

```bash
# Download site data
cd giskit/examples
./build_site_underlegger.sh "Dam 1, Amsterdam" 200 dam_site.gpkg

# Export to IFC
giskit export ifc dam_site.gpkg dam_site.ifc
```

### Example 2: Export with Recipe

```bash
# Use pre-defined export recipe
giskit export ifc dam_site.gpkg dam_onderlegger.ifc \
  --recipe export_recipes/onderlegger_only.json
```

### Example 3: Selective Layer Export

```bash
# Export only roads and water
giskit export ifc site.gpkg infrastructure.ifc \
  --layers bgt_wegdeel,bgt_waterdeel,bgt_ondersteunendwegdeel

# Export everything except parcels
giskit export ifc site.gpkg site_no_parcels.ifc \
  --exclude brk_perceel,brk_kadastrale_grens
```

### Example 4: Custom Colors via Recipe

```json
{
  "name": "Red Bike Paths",
  "input_path": "site.gpkg",
  "output_path": "site_red_bikes.ifc",
  "color_overrides": {
    "bgt_wegdeel": {
      "fietspad": [1.0, 0.0, 0.0]
    }
  }
}
```

```bash
giskit export ifc site.gpkg site.ifc --recipe my_custom_colors.json
```

### Example 5: Python API

```python
from giskit.exporters.recipe import ExportRecipe
from giskit.exporters.ifc import IfcExporter

# Create recipe
recipe = ExportRecipe(
    name="My Export",
    input_path="site.gpkg",
    output_path="site.ifc",
    layers=["bag3d_lod22", "bgt_wegdeel"],
    relative_coords=True,
    normalize_z=True
)

# Export
exporter = IfcExporter()
stats = exporter.export(recipe)
print(f"Exported {stats['total_elements']} IFC elements")
```

---

## 7. Benefits of This Approach

### Config-Driven Philosophy ✅

1. **User Customization**: Users can modify colors/materials without code changes
2. **Recipe Sharing**: Export recipes can be version controlled and shared
3. **Consistency**: Same pattern as download recipes
4. **Maintainability**: Easy to add new layers by editing YAML

### Flexibility ✅

1. **Multiple Export Modes**: Complete, onderlegger-only, buildings-only
2. **Custom Colors**: Override colors per project
3. **Layer Filtering**: Include/exclude specific layers
4. **IFC Version Support**: IFC4, IFC4X3 with automatic fallback

### Developer Experience ✅

1. **Clear Separation**: Config (YAML) vs Code (Python)
2. **Plugin System**: Easy to add new layer exporters
3. **Type Safety**: Pydantic models for validation
4. **Testing**: Config loading is easily testable

---

## 8. Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|--------------|
| 1 | Core Infrastructure | Recipe model, config loader, base classes | Working config system |
| 1 | YAML Configs | Layer mappings, colors, materials | Complete config files |
| 2 | IFC Implementation | Port exporters, materials, geometry | Working IFC export |
| 2 | CLI Integration | Add export command, recipes | CLI commands |
| 2 | Export Recipes | Example recipes, documentation | Recipe examples |
| 3 | Testing | Unit tests, integration tests | Test suite |
| 3 | Documentation | User guide, API docs | Complete docs |

**Total: ~3 weeks**

---

## 9. Success Criteria

- ✅ Export GeoPackage to IFC with correct geometry
- ✅ Layer colors loaded from YAML config
- ✅ Material names loaded from YAML config
- ✅ Export recipes for common use cases
- ✅ CLI command `giskit export ifc` working
- ✅ Custom color overrides functional
- ✅ Layer filtering (include/exclude) working
- ✅ IFC4 and IFC4X3 support with fallback
- ✅ Surface classification for BAG3D (roof/wall detection)
- ✅ Z-normalization option for buildings
- ✅ Relative vs absolute coordinate modes
- ✅ Test coverage >80%
- ✅ Documentation complete

---

## 10. Future Enhancements (Post-MVP)

1. **Export Recipe Chaining**: Link download recipe → export recipe
2. **Material Library**: Support for texture mapping
3. **LOD Selection**: Export different LODs to separate IFC files
4. **Export Presets**: Save user preferences as templates
5. **Validation**: IFC schema validation before export
6. **Progress Bars**: Rich progress indicators during export
7. **Partial Exports**: Export by bbox (subset of layers)
8. **Multi-format**: Export to other formats (glTF, CityGML)

---

## 11. Questions & Decisions

### Q1: Should we support IfcOpenShell API vs direct entity creation?

**Decision**: Use direct entity creation (like Sitedb) for control, but wrap in helper functions.

### Q2: How to handle user-provided custom exporters?

**Decision**: Plugin discovery via entry points (like pytest plugins) - Phase 2 feature.

### Q3: Should colors support alpha channel (RGBA)?

**Decision**: Yes, add optional 4th value for transparency in YAML.

### Q4: How to version export recipes?

**Decision**: Add `schema_version: "1.0"` to recipe JSON for future compatibility.

---

## 12. Notes

- **Sitedb Compatibility**: Export recipes should work with Sitedb-generated GPKGs
- **GISKit Integration**: Seamless workflow: download → export → view
- **User Feedback**: Gather user feedback on color choices for Dutch data
- **Performance**: Large exports (>1000 buildings) should show progress
- **Validation**: Validate IFC output with IfcOpenShell before saving

---

**Next Steps**: Review plan, prioritize phases, start with Phase 1 (Core Infrastructure).
