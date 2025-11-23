# py-giskit v0.1.0

First stable release of py-giskit - Recipe-driven spatial data downloader with IFC/GLB export capabilities.

## 🎯 Major Features

### IFC Export
- **IFC4+ georeferencing** with IfcMapConversion and IfcProjectedCRS (EPSG:28992)
- **Polygon interior rings** (holes) support for accurate BGT geometry
- **21 BGT layers** configured for IFC export
- **BAG3D LOD22** 3D building geometry export
- Site always at (0,0,0) with proper coordinate transformation

### GLB Export  
- **Automatic GLB conversion** from IFC via IfcConvert
- **Web viewer ready** output with world coordinates
- **No more hanging** on existing files

### Data Download
- **BGT temporal filtering** - removes terminated features (eind_registratie)
- **NEN3610 compliant** - works with all Dutch base registries
- **Recipe-based configuration** - GPKG → IFC → GLB pipeline
- **PDOK integration** - BGT, BAG3D, BAG, BRK support

## 🐛 Bug Fixes

- Filter out BGT features with `eind_registratie` (141 features removed in test case)
- Support polygon holes in IFC faces and extruded solids (`IfcArbitraryProfileDefWithVoids`)
- GLB export no longer hangs on existing files (removes before converting)
- BAG3D vertical surface handling (walls with Z-range > 0.1m)
- Added missing `bgt_ondersteunendwaterdeel` layer configuration

## 📦 Supported Datasets

### PDOK Services
- **BGT** - Basisregistratie Grootschalige Topografie (21 layers)
- **BAG3D** - 3D gebouwmodellen (LOD 1.2, 1.3, 2.2)
- **BAG** - Basisregistratie Adressen en Gebouwen
- **BRK** - Basisregistratie Kadaster

### Export Formats
- **GeoPackage** (.gpkg) - Multi-layer vector storage
- **IFC** (.ifc) - Industry Foundation Classes (IFC4X3_ADD2, IFC4, IFC2X3)
- **GLB** (.glb) - glTF Binary for web viewers

## 🚀 Usage Example

```json
{
  "name": "My Site",
  "location": {
    "type": "address",
    "value": "Curieweg 7a, Spijkenisse, Netherlands",
    "radius": 100.0
  },
  "datasets": [
    {
      "provider": "pdok",
      "service": "bag3d",
      "layers": ["lod22"],
      "temporal": "latest"
    },
    {
      "provider": "pdok",
      "service": "bgt",
      "layers": ["wegdeel", "waterdeel", "pand"],
      "temporal": "latest"
    }
  ],
  "output": {
    "path": "site.gpkg",
    "ifc_export": {
      "path": "site.ifc",
      "ifc_version": "IFC4X3_ADD2",
      "normalize_z": true,
      "glb_path": "site.glb",
      "glb_use_world_coords": true
    }
  }
}
```

```bash
giskit run recipe.json
```

## 📊 Statistics

**Test case results:**
- BGT wegdeel: 51 → 40 features (11 terminated filtered)
- Total terminated: 141 features removed
- Overlapping geometry: 16 → 0 overlaps
- IFC entities: 119 (bag3d_lod22: 11, bgt_wegdeel: 40, etc.)
- Output: 1.4 MB GPKG, 2.5 MB IFC, 5.6 MB GLB

## 🛠️ Technical Details

### NEN3610 Temporal Model
Automatically filters features with `eind_registratie` when `temporal="latest"`:
- Works for all Dutch base registries (BGT, BAG, BRK, WOZ, etc.)
- Generic implementation in OGCFeaturesProtocol
- No service-specific quirks needed

### IFC Coordinate System
- Site placement: always (0, 0, 0) - IFC best practice
- Vertex coordinates: relative to site (small local numbers)
- IfcMapConversion: RD (EPSG:28992) transformation
- Backward compatible: RD reference in properties

### Polygon Holes
- `IfcFaceBound` for B-rep interior rings
- `IfcArbitraryProfileDefWithVoids` for extruded solids
- Tested with BGT wegdeel (653 exterior + 641 interior points)

## 📝 Commits in this Release

- `4abad6a` Fix BGT temporal filter to remove terminated features
- `6eada75` Fix GLB export hanging on existing file
- `97d7e12` Add support for polygon interior rings (holes) in IFC export
- `bf44087` Add bgt_ondersteunendwaterdeel layer to IFC export configuration
- `bcc57c8` Add GLB export support to recipe IFC export config
- `d69f372` Implement IFC4+ compliant georeferencing with IfcMapConversion
- `23cc6cd` Add IFC export configuration to recipe schema
- `0d90d52` Disable BAG3D surface classification to match Sitedb approach
- `569f4f7` Fix BAG3D wall geometry export by handling vertical surface polygons

## 🙏 Credits

Developed for MAUC (mauc.nl) - Architecture, Urbanism & Construction
