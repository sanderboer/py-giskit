# Export Documentation

GISKit supports exporting geo-data to multiple formats for use in BIM software, web viewers, and game engines.

## Supported Export Formats

### IFC (Industry Foundation Classes)
- **Purpose**: BIM software (Revit, ArchiCAD, FreeCAD, Blender)
- **File extension**: `.ifc`
- **Versions**: IFC4, IFC4X3_ADD2
- **Geometry**: B-rep (IfcFacetedBrep) with semantic surfaces
- **Colors/Materials**: YAML-configurable

### GLB (glTF Binary)
- **Purpose**: Web viewers (Three.js, Cesium), Game engines (Unity, Unreal)
- **File extension**: `.glb`
- **Geometry**: Triangulated meshes
- **Colors/Materials**: Inherited from IFC
- **Requires**: IfcConvert binary

---

## IFC Export

### Quick Start

```python
from giskit.exporters.ifc import IFCExporter

# Create exporter
exporter = IFCExporter(ifc_version="IFC4X3_ADD2")

# Export GeoPackage to IFC
exporter.export(
    db_path="input.gpkg",
    output_path="output.ifc"
)
```

### Configuration

IFC export uses YAML configuration files in `giskit/config/export/`:

#### colors.yml
Defines materials and colors for different layer types:

```yaml
materials:
  roads:
    asphalt:
      color: [45, 45, 45]
      name: "Asphalt"
    concrete:
      color: [180, 180, 180]
      name: "Concrete"
  
  buildings:
    roof:
      color: [139, 69, 19]
      name: "Roof Tiles"
    wall:
      color: [210, 180, 140]
      name: "Brick"
```

#### layer_mappings.yml
Maps GeoPackage layers to IFC entities:

```yaml
layer_mappings:
  roads:
    ifc_entity: "IfcRoad"
    material: "roads.asphalt"
    layer_prefix: "wegdeel"
  
  buildings:
    ifc_entity: "IfcBuilding"
    material: "buildings.wall"
    layer_prefix: "pand"
```

### Advanced Options

```python
exporter = IFCExporter(
    ifc_version="IFC4X3_ADD2",  # or "IFC4"
    colors_config="custom_colors.yml",
    mappings_config="custom_mappings.yml"
)

exporter.export(
    db_path="input.gpkg",
    output_path="output.ifc",
    project_name="My Project",
    site_name="Amsterdam Dam Square"
)
```

---

## GLB Export

GLB export requires the IfcConvert binary from IfcOpenShell.

### Installation

#### Option 1: Auto-install (Recommended)

**Bash (Linux/macOS):**
```bash
cd bin/
./install_ifcconvert.sh
```

**Python (all platforms):**
```bash
python bin/install_ifcconvert.py
```

**With options:**
```bash
# Specific version
python bin/install_ifcconvert.py --version 0.8.4

# Force reinstall
python bin/install_ifcconvert.py --force
```

#### Option 2: Manual Download

**Linux (x86_64):**
```bash
wget https://github.com/IfcOpenShell/IfcOpenShell/releases/download/ifcconvert-0.8.4/ifcconvert-0.8.4-linux64.zip
unzip ifcconvert-0.8.4-linux64.zip -d bin/
chmod +x bin/IfcConvert
```

**macOS (ARM - M1/M2/M3):**
```bash
curl -L -o /tmp/ifcconvert.zip https://github.com/IfcOpenShell/IfcOpenShell/releases/download/ifcconvert-0.8.4/ifcconvert-0.8.4-macosm164.zip
unzip /tmp/ifcconvert.zip -d bin/
chmod +x bin/IfcConvert
```

**macOS (Intel):**
```bash
curl -L -o /tmp/ifcconvert.zip https://github.com/IfcOpenShell/IfcOpenShell/releases/download/ifcconvert-0.8.4/ifcconvert-0.8.4-macos64.zip
unzip /tmp/ifcconvert.zip -d bin/
chmod +x bin/IfcConvert
```

**Windows:**
1. Download: https://github.com/IfcOpenShell/IfcOpenShell/releases/download/ifcconvert-0.8.4/ifcconvert-0.8.4-win64.zip
2. Extract to `bin/` directory
3. Ensure `bin/IfcConvert.exe` exists

#### Option 3: Conda/Pip Install

```bash
# Conda (recommended for Python environments)
conda install -c ifcopenshell ifcopenshell

# Pip
pip install ifcopenshell
```

### Verify Installation

```python
from giskit.exporters.glb_exporter import check_ifcconvert_installation

info = check_ifcconvert_installation()
print(f"Available: {info['available']}")
print(f"Path: {info['path']}")
print(f"Version: {info['version']}")
print(f"Platform: {info['platform']}")
```

**Expected output:**
```
Available: True
Path: /path/to/bin/IfcConvert
Version: IfcOpenShell IfcConvert 0.8.4-e8eb5e4
Platform: Darwin arm64
```

### Quick Start

```python
from giskit.exporters.glb_exporter import convert_ifc_to_glb
from pathlib import Path

# Convert IFC to GLB
convert_ifc_to_glb(
    ifc_path=Path("input.ifc"),
    glb_path=Path("output.glb")
)
```

### Advanced Options

```python
from giskit.exporters.glb_exporter import GLBExporter

exporter = GLBExporter()

# Check if available
if not exporter.is_available():
    print(exporter.get_install_instructions())
    exit(1)

# Convert with custom options
exporter.ifc_to_glb(
    ifc_path=Path("input.ifc"),
    glb_path=Path("output.glb"),
    use_world_coords=True,    # Preserve geo-coordinates
    generate_uvs=True,        # For textures
    center_model=False        # Keep original position
)
```

### IfcConvert Options

| Option | Default | Description |
|--------|---------|-------------|
| `use_world_coords` | `True` | Use world coordinates (preserves geo-location) |
| `generate_uvs` | `True` | Generate UV coordinates for textures |
| `center_model` | `False` | Center model at origin (useful for web viewers) |

---

## Complete Pipeline

### GeoPackage → IFC → GLB

```python
from pathlib import Path
from giskit.exporters.ifc import IFCExporter
from giskit.exporters.glb_exporter import convert_ifc_to_glb

# Paths
gpkg_path = Path("data/input.gpkg")
ifc_path = Path("data/output.ifc")
glb_path = Path("data/output.glb")

# Step 1: GeoPackage → IFC
print("Step 1: Exporting to IFC...")
exporter = IFCExporter(ifc_version="IFC4X3_ADD2")
exporter.export(gpkg_path, ifc_path)

# Step 2: IFC → GLB
print("Step 2: Converting to GLB...")
convert_ifc_to_glb(ifc_path, glb_path)

print(f"✓ Complete! GLB available at: {glb_path}")
```

---

## Platform-Specific Notes

### Linux
- **Binary location**: `bin/IfcConvert`
- **Make executable**: `chmod +x bin/IfcConvert`
- **Dependencies**: Usually none (statically linked)

### macOS
- **ARM (M1/M2/M3)**: Use `macosm164` version
- **Intel**: Use `macos64` version
- **Security**: First run may require: `System Preferences > Security & Privacy > Allow`
- **Binary location**: `bin/IfcConvert`

### Windows
- **Binary location**: `bin\IfcConvert.exe`
- **PATH**: Add `bin\` to system PATH for global access
- **Dependencies**: Visual C++ Redistributable (usually pre-installed)

---

## Docker Support

See `Dockerfile.export` for a sample Docker setup with IfcConvert pre-installed.

```bash
# Build Docker image
docker build -f Dockerfile.export -t giskit-export .

# Run export in container
docker run -v $(pwd)/data:/data giskit-export \
    python -c "
from giskit.exporters.ifc import IFCExporter
exporter = IFCExporter()
exporter.export('/data/input.gpkg', '/data/output.ifc')
"
```

---

## Troubleshooting

### IfcConvert Not Found

**Error:**
```
RuntimeError: IfcConvert not found. Install with:
  python bin/install_ifcconvert.py
```

**Solution:**
1. Run installer: `python bin/install_ifcconvert.py`
2. Or manually download for your platform (see Installation above)
3. Verify: `python -c "from giskit.exporters.glb_exporter import check_ifcconvert_installation; print(check_ifcconvert_installation())"`

### Permission Denied (Linux/macOS)

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'bin/IfcConvert'
```

**Solution:**
```bash
chmod +x bin/IfcConvert
```

### Wrong Architecture (macOS)

**Error:**
```
Bad CPU type in executable
```

**Solution:**
- Check your Mac architecture: `uname -m`
- ARM (M1/M2/M3): Use `macosm164` version
- Intel: Use `macos64` version
- Reinstall: `python bin/install_ifcconvert.py --force`

### Large File Size

GLB files can be larger than IFC due to triangulation.

**Solutions:**
1. **Draco compression** (future feature)
2. **Reduce geometry detail** before IFC export
3. **Use web-optimized formats** (glTF with separate bin/textures)

---

## Performance

### Test Results (486 entities from test_dam.gpkg)

| Format | Size | Export Time | Notes |
|--------|------|-------------|-------|
| IFC | 6.3 MB | 8s | B-rep geometry, semantic faces |
| GLB | 12.4 MB | 5s | Triangulated meshes, materials preserved |

### Recommendations

- **Small projects** (<1000 entities): Direct export
- **Medium projects** (1000-10000): Batch by layer type
- **Large projects** (>10000): Consider LOD reduction or tiling

---

## Examples

See test scripts:
- `test_ifc_export.py` - Complete IFC export example
- `test_glb_export.py` - IFC to GLB conversion example

### Recipe-based Export

```python
from giskit.exporters.ifc import IFCExporter

# Use existing GISKit recipe
exporter = IFCExporter()
exporter.export(
    db_path="data/curieweg_complete.gpkg",
    output_path="data/curieweg.ifc",
    project_name="Curieweg Infrastructure",
    site_name="Curieweg, Amsterdam"
)
```

---

## API Reference

### IFCExporter

```python
class IFCExporter:
    def __init__(
        self,
        ifc_version: str = "IFC4X3_ADD2",
        colors_config: Optional[Path] = None,
        mappings_config: Optional[Path] = None
    )
    
    def export(
        self,
        db_path: Path,
        output_path: Path,
        project_name: str = "GISKit Export",
        site_name: str = "Site"
    ) -> None
```

### GLBExporter

```python
class GLBExporter:
    def __init__(self)
    
    def is_available(self) -> bool
    
    def ifc_to_glb(
        self,
        ifc_path: Path,
        glb_path: Path,
        use_world_coords: bool = True,
        generate_uvs: bool = True,
        center_model: bool = False
    ) -> None

def convert_ifc_to_glb(
    ifc_path: Path,
    glb_path: Path,
    **options
) -> None

def check_ifcconvert_installation() -> dict
```

---

## Related Documentation

- [IFC Export Architecture](PLAN_IFC_EXPORT.md)
- [Color/Material System](giskit/config/export/colors.yml)
- [Layer Mappings](giskit/config/export/layer_mappings.yml)
- [GISKit Recipes](giskit/recipes/README.md)
