# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- GLB export for 3D visualization (requires IfcConvert)
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

## [0.1.0-dev] - 2024-11-23

### Added
- Initial development version
- Core architecture and protocols
- PDOK integration
- Recipe schema and validation
- Test infrastructure

[Unreleased]: https://github.com/a190/giskit/compare/v0.1.0...HEAD
[0.1.0-dev]: https://github.com/a190/giskit/releases/tag/v0.1.0-dev
