"""OBJ+MTL per-layer exporter packed as a ZIP.

Exports IFC file to layered OBJ+MTL format using ifcopenshell.geom for proper tessellation.
Uses the same geometry extraction as GLB exporter for consistency.
"""

from __future__ import annotations

import json
import zipfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ifcopenshell
import ifcopenshell.geom
import numpy as np


class OBJZipExporter:
    """Export IFC to layered OBJ+MTL ZIP using ifcopenshell.geom.

    Uses ifcopenshell.geom for proper triangulation and tessellation,
    ensuring good quality geometry output.
    """

    def __init__(self):
        """Initialize OBJ ZIP exporter."""
        pass

    def is_available(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import ifcopenshell.geom  # noqa: F401

            return True
        except ImportError:
            return False

    def ifc_to_obj_zip(
        self,
        ifc_path: Path,
        output_zip_path: Path,
        use_world_coords: bool = True,
    ) -> None:
        """Convert IFC file to OBJ+MTL ZIP using ifcopenshell.geom.

        Args:
            ifc_path: Input IFC file path
            output_zip_path: Output ZIP file path
            use_world_coords: Use world coordinates (default: True)

        Raises:
            RuntimeError: If dependencies are not available
            Exception: If conversion fails
        """
        if not self.is_available():
            raise RuntimeError(
                "OBJ export requires ifcopenshell. Install with: pip install ifcopenshell"
            )

        print(f"Converting IFC to OBJ ZIP: {ifc_path} → {output_zip_path}")
        print("  Using ifcopenshell.geom for proper tessellation")

        # Open IFC file
        ifc_file = ifcopenshell.open(str(ifc_path))

        # Configure geometry settings
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", use_world_coords)
        settings.set("weld-vertices", True)

        # Extract geometry from IFC, grouped by layer
        print("  Extracting geometry...")
        layers_data = self._extract_geometry_by_layer(ifc_file, settings)

        if not layers_data:
            raise RuntimeError("No geometry found in IFC file")

        print(f"  Extracted {len(layers_data)} layer(s)")

        # Build OBJ ZIP
        print("  Building OBJ ZIP...")
        self._build_obj_zip(layers_data, output_zip_path)

        print(f"✓ OBJ ZIP export complete: {output_zip_path}")

        # Show file size
        if output_zip_path.exists():
            zip_mb = output_zip_path.stat().st_size / (1024 * 1024)
            print(f"  ZIP size: {zip_mb:.1f} MB")

    def _extract_geometry_by_layer(
        self, ifc_file: Any, settings: Any
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract geometry from IFC file, grouped by layer/class.

        Args:
            ifc_file: IFC file object
            settings: Geometry settings

        Returns:
            Dict mapping layer name to list of mesh dicts
            - Each mesh has: vertices (Nx3 array), indices (array), material_id, color
        """
        layers_data: Dict[str, List[Dict[str, Any]]] = {}

        # Create geometry iterator
        iterator = ifcopenshell.geom.iterator(settings, ifc_file, num_threads=1)

        if iterator.initialize():
            while True:
                shape = iterator.get()
                # Get product by GUID
                product = ifc_file.by_guid(shape.guid)  # type: ignore

                # Determine layer name from product name or class
                layer_name = self._get_layer_name(product)

                # Get geometry
                geometry = shape.geometry  # type: ignore

                # Get vertices (flat array of floats: x1,y1,z1,x2,y2,z2,...)
                verts = geometry.verts  # type: ignore
                vertices = np.array(verts).reshape(-1, 3)

                # Get faces (flat array of ints: i1,i2,i3,i4,i5,i6,...)
                faces = geometry.faces  # type: ignore
                indices = np.array(faces, dtype=np.uint32)

                # Get material/color
                material_id, color = self._get_material_and_color(product, geometry)

                # Store mesh in layer
                if layer_name not in layers_data:
                    layers_data[layer_name] = []

                layers_data[layer_name].append(
                    {
                        "vertices": vertices,
                        "indices": indices,
                        "material_id": material_id,
                        "color": color,
                        "name": product.Name or f"{product.is_a()}_{product.id()}",
                    }
                )

                if not iterator.next():
                    break

        return layers_data

    def _get_layer_name(self, product: Any) -> str:
        """Determine layer name from IFC product.

        Extracts layer name from property sets (Pset_BGT_*, Pset_BAG3D_*)
        or from product name patterns.
        """
        # Try to get layer from property sets (most reliable for giskit exports)
        try:
            import ifcopenshell.util.element

            psets = ifcopenshell.util.element.get_psets(product)
            for pset_name in psets.keys():
                # BGT layers: Pset_BGT_Wegdeel -> bgt_wegdeel
                if pset_name.startswith("Pset_BGT_"):
                    layer_type = pset_name.replace("Pset_BGT_", "").lower()
                    return f"bgt_{layer_type}"
                # BAG3D layers: Pset_BAG3D_* -> bag3d_lod22
                elif pset_name.startswith("Pset_BAG3D_"):
                    return "bag3d_lod22"
        except Exception:
            pass

        # Fallback: try to extract from product name
        if hasattr(product, "Name") and product.Name:
            name = product.Name
            # BAG3D pattern: "NL.IMBAG.Pand.xxx_roof" -> bag3d_lod22
            if name.startswith("NL.IMBAG.Pand."):
                return "bag3d_lod22"

        # Final fallback to IFC class
        return product.is_a()

    def _get_material_and_color(
        self, product: Any, geometry: Any
    ) -> Tuple[str, Tuple[float, float, float, float]]:
        """Get material ID and color from product/geometry.

        Returns:
            Tuple of (material_id, (r, g, b, a))
        """
        # Try to get material from IFC
        if hasattr(product, "HasAssociations"):
            for association in product.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if hasattr(material, "Name") and material.Name:
                        material_id = f"mat_{material.Name}"
                        color = self._extract_color_from_geometry(geometry)
                        return material_id, color

        # Try to get from style/geometry
        if hasattr(geometry, "materials") and geometry.materials:
            mat = geometry.materials[0]

            # Get material name
            if hasattr(mat, "original_name") and mat.original_name():
                material_id = f"mat_{mat.original_name()}"
            else:
                material_id = f"mat_{product.is_a()}"

            # Get color
            color = self._extract_color_from_material(mat)
            return material_id, color

        # Default
        material_id = f"mat_{product.is_a()}"
        color = (0.8, 0.8, 0.8, 1.0)
        return material_id, color

    def _extract_color_from_material(self, mat: Any) -> Tuple[float, float, float, float]:
        """Extract RGBA color from material."""
        if hasattr(mat, "diffuse"):
            color = mat.diffuse
            r = color.r() if callable(getattr(color, "r", None)) else 0.8
            g = color.g() if callable(getattr(color, "g", None)) else 0.8
            b = color.b() if callable(getattr(color, "b", None)) else 0.8
            return (r, g, b, 1.0)
        return (0.8, 0.8, 0.8, 1.0)

    def _extract_color_from_geometry(self, geometry: Any) -> Tuple[float, float, float, float]:
        """Extract RGBA color from geometry materials."""
        if hasattr(geometry, "materials") and geometry.materials:
            mat = geometry.materials[0]
            return self._extract_color_from_material(mat)
        return (0.8, 0.8, 0.8, 1.0)

    def _build_obj_zip(
        self, layers_data: Dict[str, List[Dict[str, Any]]], output_zip_path: Path
    ) -> None:
        """Build OBJ ZIP file from layers data.

        Args:
            layers_data: Dict mapping layer name to list of meshes
            output_zip_path: Output ZIP file path
        """
        output_zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_layers = []

            for layer_name, meshes in sorted(layers_data.items()):
                if not meshes:
                    continue

                print(f"    - {layer_name} ({len(meshes)} mesh(es))...")

                # Merge all meshes in layer into single OBJ
                obj_text, materials = self._build_layer_obj(layer_name, meshes)

                # Write OBJ and MTL files
                obj_filename = f"{layer_name}.obj"
                mtl_filename = f"{layer_name}.mtl"

                mtl_text = self._build_mtl(materials)

                zf.writestr(obj_filename, obj_text)
                zf.writestr(mtl_filename, mtl_text)

                manifest_layers.append(
                    {
                        "name": layer_name,
                        "obj": obj_filename,
                        "mtl": mtl_filename,
                        "mesh_count": len(meshes),
                    }
                )

            # Write manifest
            manifest = {
                "version": "1.0",
                "generator": "giskit OBJZipExporter (ifcopenshell.geom)",
                "layers": manifest_layers,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    def _build_layer_obj(
        self, layer_name: str, meshes: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Tuple[float, float, float, float]]]:
        """Build OBJ text for a layer from multiple meshes.

        Args:
            layer_name: Layer name
            meshes: List of mesh dicts with vertices, indices, material_id, color

        Returns:
            Tuple of (obj_text, materials_dict)
        """
        buf = StringIO()

        # Header
        buf.write("# giskit OBJ export (ifcopenshell.geom)\n")
        buf.write(f"# layer: {layer_name}\n")
        buf.write(f"mtllib {layer_name}.mtl\n\n")

        # Track materials
        materials: Dict[str, Tuple[float, float, float, float]] = {}

        # Merge all meshes
        vertex_offset = 0

        for mesh in meshes:
            vertices = mesh["vertices"]
            indices = mesh["indices"]
            material_id = mesh["material_id"]
            color = mesh["color"]

            # Remember material
            if material_id not in materials:
                materials[material_id] = color

            # Write vertices
            for v in vertices:
                buf.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write faces (OBJ is 1-indexed)
            buf.write(f"usemtl {material_id}\n")
            for i in range(0, len(indices), 3):
                i1 = indices[i] + vertex_offset + 1
                i2 = indices[i + 1] + vertex_offset + 1
                i3 = indices[i + 2] + vertex_offset + 1
                buf.write(f"f {i1} {i2} {i3}\n")

            # Update offset for next mesh
            vertex_offset += len(vertices)

            buf.write("\n")

        return buf.getvalue(), materials

    def _build_mtl(self, materials: Dict[str, Tuple[float, float, float, float]]) -> str:
        """Build MTL text from materials dict.

        Args:
            materials: Dict mapping material_id to (r, g, b, a)

        Returns:
            MTL text
        """
        buf = StringIO()
        buf.write("# giskit OBJ materials\n\n")

        for material_id, (r, g, b, a) in sorted(materials.items()):
            buf.write(f"newmtl {material_id}\n")
            buf.write(f"Kd {r:.6f} {g:.6f} {b:.6f}\n")
            buf.write(f"d {a:.6f}\n")
            buf.write("illum 2\n")
            buf.write("\n")

        return buf.getvalue()
