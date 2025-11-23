"""IFC exporter for GeoPackage data.

Exports GeoPackage layers to IFC format with YAML-configured colors and materials.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import ifcopenshell
import ifcopenshell.api

from .layer_exporter import LayerExporter
from .materials import MaterialsManager
from .schema_adapter import get_schema_adapter


class IFCExporter:
    """Export GeoPackage to IFC format."""

    def __init__(
        self,
        ifc_version: str = "IFC4X3_ADD2",
        author: str = "GISKit",
        organization: str = "A190",
        materials_manager: Optional[MaterialsManager] = None,
    ):
        """Initialize IFC exporter.

        Args:
            ifc_version: IFC schema version (IFC4X3_ADD2, IFC4, IFC2X3)
            author: Author name for IFC metadata
            organization: Organization name for IFC metadata
            materials_manager: Optional MaterialsManager (creates default if None)
        """
        # Type narrowing for IFC schema
        schema: Any = ifc_version
        self.ifc = ifcopenshell.file(schema=schema)
        self.author = author
        self.organization = organization

        # Materials manager
        self.materials = materials_manager if materials_manager else MaterialsManager()

        # Schema adapter for version-specific logic
        self.schema_adapter = get_schema_adapter(self.ifc)

        # Layer exporter
        self.layer_exporter = LayerExporter(self.materials)

        # IFC context and units
        self.project: Any = None
        self.site: Any = None
        self.context: Any = None

        # Reference point (will be set from metadata or first feature)
        self.ref_x: float = 0.0
        self.ref_y: float = 0.0

    def export(
        self,
        db_path: Path,
        output_path: Path,
        layers: Optional[List[str]] = None,
        exclude_layers: Optional[List[str]] = None,
        relative: bool = True,
        normalize_z: bool = True,
        site_name: str = "Site",
        ref_x: Optional[float] = None,
        ref_y: Optional[float] = None,
    ) -> None:
        """Export GeoPackage to IFC file.

        Args:
            db_path: Path to GeoPackage database
            output_path: Output IFC file path
            layers: List of layer names to export (None = all supported)
            exclude_layers: List of layer names to exclude
            relative: Use relative coordinates (True) or absolute RD (False)
            normalize_z: Normalize 3D building Z coordinates to ground level
            site_name: Name for the IFC site
            ref_x: Reference point X (auto-detect if None)
            ref_y: Reference point Y (auto-detect if None)
        """
        print(f"Exporting to IFC: {output_path}")

        # Set reference point
        if ref_x is not None and ref_y is not None:
            self.ref_x = ref_x
            self.ref_y = ref_y
        else:
            # Auto-detect from first feature's centroid
            self.ref_x, self.ref_y = self._auto_detect_reference_point(db_path, layers)

        print(f"  Reference point: ({self.ref_x:.2f}, {self.ref_y:.2f})")
        print(f"  Coordinate mode: {'relative' if relative else 'absolute'}")
        print(f"  Z-normalization: {'enabled' if normalize_z else 'disabled'}")

        # Create IFC structure
        self._create_project(site_name)
        self._create_site(site_name)

        # Determine which layers to export
        if layers is None:
            layers = self._get_available_layers(db_path)

        # Filter out excluded layers
        if exclude_layers:
            layers = [layer for layer in layers if layer not in exclude_layers]

        # Filter to only supported layers
        supported_layers = [
            layer for layer in layers if self.materials.get_layer_config(layer) is not None
        ]

        print(f"  Exporting {len(supported_layers)} layer(s)...")

        # Statistics
        total_stats: Dict[str, int] = {}

        # Export each layer
        for layer in supported_layers:
            print(f"    - {layer}...")

            try:
                stats = self.layer_exporter.export(
                    layer_name=layer,
                    ifc_file=self.ifc,
                    site=self.site,
                    context=self.context,
                    schema_adapter=self.schema_adapter,
                    db_path=str(db_path),
                    ref_x=self.ref_x,
                    ref_y=self.ref_y,
                    relative=relative,
                    normalize_z=normalize_z,
                )
                # Accumulate stats
                for key, count in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + count
                print(f"      ✓ Exported {sum(stats.values())} entities")
            except Exception as e:
                print(f"      ✗ Error: {e}")
                import traceback

                traceback.print_exc()

        # Write IFC file
        self.ifc.write(str(output_path))
        print(f"✓ Exported to {output_path}")

        # Print statistics
        print(f"  Total entities: {sum(total_stats.values())}")
        for entity_type, count in sorted(total_stats.items()):
            print(f"    - {entity_type}: {count}")

    def _create_project(self, site_name: str) -> None:
        """Create IFC Project with metadata."""
        # Create project using API
        self.project = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc,
            ifc_class="IfcProject",
            name=f"GISKit Export - {site_name}",
        )

        # Set project metadata
        person = self.ifc.createIfcPerson(None, self.author, None, None, None, None, None, None)

        organization_entity = self.ifc.createIfcOrganization(
            None, self.organization, None, None, None
        )

        person_and_org = self.ifc.createIfcPersonAndOrganization(person, organization_entity, None)

        application = self.ifc.createIfcApplication(
            organization_entity, "1.0", "GISKit IFC Exporter", "GISKit"
        )

        owner_history = self.ifc.createIfcOwnerHistory(
            person_and_org,
            application,
            None,
            "ADDED",
            None,
            None,
            None,
            int(datetime.now().timestamp()),
        )

        self.project.OwnerHistory = owner_history

        # Create geometric representation context
        self.context = self.ifc.createIfcGeometricRepresentationContext(
            None,
            "Model",
            3,
            1.0e-5,
            self.ifc.createIfcAxis2Placement3D(
                self.ifc.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None
            ),
            None,
        )

        # Set units (meters, square meters, cubic meters)
        units = [
            self.ifc.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE"),
            self.ifc.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE"),
            self.ifc.createIfcSIUnit(None, "VOLUMEUNIT", None, "CUBIC_METRE"),
        ]

        unit_assignment = self.ifc.createIfcUnitAssignment(units)
        self.project.UnitsInContext = unit_assignment

        # Add context to project
        self.project.RepresentationContexts = [self.context]

    def _create_site(self, site_name: str) -> None:
        """Create IFC Site with geo-referencing."""
        # Create site
        self.site = ifcopenshell.api.run(
            "root.create_entity", self.ifc, ifc_class="IfcSite", name=site_name
        )

        # Set site location (reference point in RD coordinates)
        # NOTE: This uses Amersfoort RD New (EPSG:28992)
        # The LocalPlacement origin should be at the reference point (e.g., site address)
        site_location = self.ifc.createIfcSite(
            self.site.GlobalId,
            self.site.OwnerHistory if hasattr(self.site, "OwnerHistory") else None,
            self.site.Name,
            None,  # Description
            None,  # ObjectType
            self.ifc.createIfcLocalPlacement(
                None,
                self.ifc.createIfcAxis2Placement3D(
                    self.ifc.createIfcCartesianPoint((self.ref_x, self.ref_y, 0.0)), None, None
                ),
            ),
            None,  # Representation
            None,  # LongName
            None,  # CompositionType
            None,  # RefLatitude
            None,  # RefLongitude
            None,  # RefElevation
            None,  # LandTitleNumber
            None,  # SiteAddress
        )

        # Replace site entity
        self.ifc.remove(self.site)
        self.site = site_location

        # Assign site to project
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc, relating_object=self.project, products=[self.site]
        )

    def _get_available_layers(self, db_path: Path) -> List[str]:
        """Get list of available layers in GeoPackage."""
        import fiona

        try:
            layers = fiona.listlayers(str(db_path))
            return layers
        except Exception as e:
            print(f"Warning: Could not list layers: {e}")
            return []

    def _auto_detect_reference_point(
        self, db_path: Path, layers: Optional[List[str]] = None
    ) -> tuple[float, float]:
        """Auto-detect reference point from metadata or first feature's centroid.

        Args:
            db_path: Path to GeoPackage
            layers: Optional list of layers to check

        Returns:
            Tuple of (ref_x, ref_y)
        """
        import geopandas as gpd

        # First try to read from _metadata table (created by giskit)
        try:
            metadata_gdf = gpd.read_file(str(db_path), layer="_metadata")
            if len(metadata_gdf) > 0 and "x" in metadata_gdf.columns and "y" in metadata_gdf.columns:
                ref_x = float(metadata_gdf["x"].iloc[0])
                ref_y = float(metadata_gdf["y"].iloc[0])
                print(f"  Using reference point from _metadata: ({ref_x:.2f}, {ref_y:.2f})")
                return (ref_x, ref_y)
        except Exception:
            # _metadata table doesn't exist or is invalid, fall back to auto-detection
            pass

        if layers is None:
            layers = self._get_available_layers(db_path)

        # Try to find a feature with geometry
        for layer in layers:
            try:
                gdf = gpd.read_file(str(db_path), layer=layer, rows=1)
                if len(gdf) > 0 and gdf.geometry.iloc[0] is not None:
                    centroid = gdf.geometry.iloc[0].centroid
                    return (centroid.x, centroid.y)
            except Exception:
                continue

        # Default to origin if no features found
        return (0.0, 0.0)
