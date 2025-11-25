# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **GLB Export**: Now uses `ifcopenshell.geom` Python API instead of external IfcConvert binary - eliminates binary dependency and simplifies installation
- **IFC Export Structure**: Building surfaces (roof/wall/floor) now exported as separate `IfcBuildingElementProxy` elements instead of multiple representations on a single `IfcBuilding` - improves compatibility with Blender and other BIM tools

### Added
- **Klimaateffectatlas Provider** (26 climate services): Heat stress, flooding risk, drought, temperature extremes, and nature/biodiversity data for climate adaptation planning
  - Heat Stress (6): Social vulnerability, heat island effect, perceived temperature, cooling access, shade maps, elderly vulnerability
  - Flooding Risk (9): Precipitation extremes (current + 2050 scenarios), safe zones, dry floors, groundwater flooding risk
  - Drought Risk (4): Precipitation deficit scenarios, nature drought sensitivity, water salinization
  - Urban (4): Green/paved/water percentages, municipality boundaries
  - Temperature (2): Frost days (current + 2050)
  - Nature (1): BKNS biodiversity classification
  - Recipe: `woningbouw_klimaat_risico_analyse.json` - comprehensive climate risk assessment for housing development
  - Recipe: `amsterdam_klimaat_check.json` - example climate analysis for Amsterdam
- **WFS Protocol**: Traditional WFS 2.0 support with automatic bbox CRS transformation (WGS84 → service CRS)
- **GLB Compression**: Automatic gzip compression for GLB exports (83% file size reduction) - enabled by default via `glb_compress: true` in export config
- **Grid Subdivision for Large Downloads**: BAG3D downloads now automatically subdivide large bounding boxes into smaller grid cells with concurrent processing - dramatically improves performance and reliability for large areas
- **CLI Version Shorthand**: Added `-v` flag as shorthand for `--version`
- **Color Customization**: Support for custom colors in IFC/GLB exports via `colors` field in export config

### Fixed
- **CRITICAL**: WFS protocol bbox transformation - now correctly transforms from WGS84 to service's native CRS (e.g., EPSG:28992)
- **GLB Material Export**: GLB files now correctly show multiple materials (red roofs, beige walls, gray floors) instead of merging all surfaces into a single red material - uses color-based material IDs to preserve distinct materials
- **IFC Blender Compatibility**: IFC files now display all building surfaces (roof/wall/floor) in Blender instead of only the first surface - each surface is now a separate element

### Added (v0.1.0)
- Initial release of GISKit
- Recipe-driven spatial data download system
- PDOK provider with 53 services (vector, aerial imagery, elevation)
- OGC Features API protocol support
- WMTS (Web Map Tile Service) protocol support
- WCS (Web Coverage Service) protocol support
- CityJSON format support for 3D building data (BAG3D)
- Automatic CRS transformation
- GeoPackage output format
- IFC export for BIM workflows
- GLB export for 3D visualization (uses ifcopenshell.geom)
- CLI interface with `giskit` command
- Quirks system for provider-specific API handling
- Comprehensive test suite (117 tests)
- Full documentation and examples

### PDOK Services
- **Vector Data**: BGT (54 layers), BAG, BRK, BAG3D, CBS statistics, NWB
- **Aerial Imagery**: Luchtfoto (6 layers), Satellietbeeld (3 layers), BRT (4 layers)
- **Elevation Data**: AHN4 DTM/DSM at 0.5m resolution

### Dependencies
- Python 3.10+
- httpx for async HTTP requests
- geopandas for spatial data handling
- shapely for geometric operations
- pyproj for coordinate transformations
- pydantic for data validation
- typer for CLI
- ifcopenshell (optional) for IFC/GLB export
- pygltflib (optional) for GLB generation
- numpy for geometry processing

## [0.1.0-dev] - 2024-11-23

### Added
- Initial development version
- Core architecture and protocols
- PDOK integration
- Recipe schema and validation
- Test infrastructure

[Unreleased]: https://github.com/a190/giskit/compare/v0.1.0...HEAD
[0.1.0-dev]: https://github.com/a190/giskit/releases/tag/v0.1.0-dev
