#!/usr/bin/env python3
"""
Sample export pipeline for Docker deployment.

This script demonstrates a complete GeoPackage → IFC → GLB pipeline
that can be run inside a Docker container.

REQUIREMENTS:
    This example requires ifcopenshell to be installed:
    - pip install giskit[ifc]
    - or: pip install ifcopenshell

Usage (inside Docker):
    python /data/export_pipeline.py /data/input.gpkg /data/output

Usage (local):
    python export_pipeline.py data/input.gpkg data/output
"""

import sys
from pathlib import Path

try:
    from giskit.exporters.glb_exporter import check_ifcconvert_installation, convert_ifc_to_glb
    from giskit.exporters.ifc import IFCExporter
except ImportError as e:
    print("ERROR: This example requires ifcopenshell to be installed")
    print()
    print("Install using pip:")
    print("  pip install giskit[ifc]")
    print()
    print("Or install ifcopenshell separately:")
    print("  pip install ifcopenshell")
    print()
    print(f"Import error: {e}")
    sys.exit(1)


def export_pipeline(input_gpkg: Path, output_dir: Path):
    """Run complete export pipeline.

    Args:
        input_gpkg: Input GeoPackage file
        output_dir: Output directory for IFC and GLB files
    """
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output paths
    stem = input_gpkg.stem
    ifc_path = output_dir / f"{stem}.ifc"
    glb_path = output_dir / f"{stem}.glb"

    print("=" * 70)
    print("GISKit Export Pipeline")
    print("=" * 70)
    print(f"Input:  {input_gpkg}")
    print(f"Output: {output_dir}")
    print()

    # Check IfcConvert availability
    print("Checking IfcConvert installation...")
    info = check_ifcconvert_installation()
    print(f"  Available: {info['available']}")
    print(f"  Path: {info['path']}")
    print(f"  Version: {info['version']}")
    print(f"  Platform: {info['platform']}")
    print()

    if not info["available"]:
        print("ERROR: IfcConvert not found!")
        print("In Docker, this should be pre-installed.")
        print("For local use, run: python bin/install_ifcconvert.py")
        sys.exit(1)

    # Step 1: Export to IFC
    print("-" * 70)
    print("Step 1: GeoPackage → IFC")
    print("-" * 70)

    exporter = IFCExporter(ifc_version="IFC4X3_ADD2")

    print(f"Exporting {input_gpkg} to {ifc_path}...")
    exporter.export(db_path=input_gpkg, output_path=ifc_path, site_name=stem)

    if ifc_path.exists():
        ifc_mb = ifc_path.stat().st_size / (1024 * 1024)
        print(f"✓ IFC export complete: {ifc_path}")
        print(f"  Size: {ifc_mb:.2f} MB")
    else:
        print("✗ IFC export failed!")
        sys.exit(1)

    print()

    # Step 2: Convert to GLB
    print("-" * 70)
    print("Step 2: IFC → GLB")
    print("-" * 70)

    print(f"Converting {ifc_path} to {glb_path}...")
    convert_ifc_to_glb(
        ifc_path=ifc_path,
        glb_path=glb_path,
        use_world_coords=True,
        generate_uvs=True,
        center_model=False,
    )

    if glb_path.exists():
        glb_mb = glb_path.stat().st_size / (1024 * 1024)
        print(f"✓ GLB export complete: {glb_path}")
        print(f"  Size: {glb_mb:.2f} MB")
    else:
        print("✗ GLB export failed!")
        sys.exit(1)

    print()
    print("=" * 70)
    print("Pipeline Complete!")
    print("=" * 70)
    print(f"IFC: {ifc_path} ({ifc_mb:.2f} MB)")
    print(f"GLB: {glb_path} ({glb_mb:.2f} MB)")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python export_pipeline.py <input.gpkg> <output_dir>")
        print()
        print("Examples:")
        print("  python export_pipeline.py data/test.gpkg data/output")
        print("  docker run -v $(pwd)/data:/data giskit-export \\")
        print("    python /data/export_pipeline.py /data/test.gpkg /data/output")
        sys.exit(1)

    input_gpkg = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not input_gpkg.exists():
        print(f"ERROR: Input file not found: {input_gpkg}")
        sys.exit(1)

    export_pipeline(input_gpkg, output_dir)


if __name__ == "__main__":
    main()
