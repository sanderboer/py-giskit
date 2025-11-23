"""GLB exporter using IfcConvert (IfcOpenShell).

Converts IFC to GLB (glTF binary) format for web viewers.
Uses IfcConvert command-line tool for best BAG3D quality.

REQUIREMENTS:
    This module requires IfcOpenShell to be installed, which provides
    the IfcConvert binary for IFC → GLB conversion.

Installation:
    # Install giskit with IFC support
    pip install giskit[ifc]

    # Or install ifcopenshell separately
    pip install ifcopenshell
"""

import platform as platform_module
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def get_binary_name() -> str:
    """Get platform-specific binary name for IfcConvert."""
    system = platform_module.system()
    if system == "Windows":
        return "IfcConvert.exe"
    return "IfcConvert"


def find_ifcconvert_binary() -> Optional[str]:
    """Find IfcConvert binary in common locations.

    Search order:
    1. System PATH
    2. Project bin/ directory (platform-specific binary)
    3. Common installation paths

    Returns:
        Path to IfcConvert binary, or None if not found
    """
    binary_name = get_binary_name()

    # 1. Check system PATH
    path_binary = shutil.which("IfcConvert")
    if path_binary:
        return path_binary

    # 2. Check project bin/ directory
    # Go up from giskit/exporters/glb_exporter.py to project root
    project_root = Path(__file__).parent.parent.parent.parent
    bin_dir = project_root / "bin"
    local_binary = bin_dir / binary_name

    if local_binary.exists() and local_binary.is_file():
        return str(local_binary)

    # 3. Check common installation paths (Unix-like systems)
    if platform_module.system() != "Windows":
        common_paths = [
            "/opt/conda/bin/IfcConvert",
            "/usr/local/bin/IfcConvert",
            "/usr/bin/IfcConvert",
            str(Path.home() / ".local" / "bin" / "IfcConvert"),
        ]
        for path in common_paths:
            if Path(path).exists():
                return path

    return None


class GLBExporter:
    """Export IFC to GLB using IfcConvert."""

    def __init__(self):
        """Initialize GLB exporter."""
        self.ifcconvert_path = find_ifcconvert_binary()

    def is_available(self) -> bool:
        """Check if IfcConvert is available."""
        return self.ifcconvert_path is not None

    def get_install_instructions(self) -> str:
        """Get installation instructions for current platform."""
        instructions = [
            "IfcConvert not found. Install ifcopenshell to get IfcConvert:",
            "",
            "Install giskit with IFC support:",
            "  pip install giskit[ifc]",
            "",
            "Or install ifcopenshell separately:",
            "  pip install ifcopenshell",
        ]

        return "\n".join(instructions)

    def ifc_to_glb(
        self,
        ifc_path: Path,
        glb_path: Path,
        use_world_coords: bool = True,
        generate_uvs: bool = True,
        center_model: bool = False,
    ) -> None:
        """Convert IFC file to GLB using IfcConvert.

        Args:
            ifc_path: Input IFC file path
            glb_path: Output GLB file path
            use_world_coords: Use world coordinates (default: True)
            generate_uvs: Generate UV coordinates (default: True)
            center_model: Center model at origin (default: False)

        Raises:
            RuntimeError: If IfcConvert is not available
            subprocess.CalledProcessError: If conversion fails
        """
        if not self.is_available():
            raise RuntimeError(self.get_install_instructions())

        print(f"Converting IFC to GLB: {ifc_path} → {glb_path}")
        print(f"  Using IfcConvert: {self.ifcconvert_path}")

        # Remove existing GLB file to avoid interactive prompt from IfcConvert
        if glb_path.exists():
            glb_path.unlink()

        # Build IfcConvert command
        cmd = [
            str(self.ifcconvert_path),
            str(ifc_path),
            str(glb_path),
        ]

        # Add options
        if use_world_coords:
            cmd.append("--use-world-coords")

        if generate_uvs:
            cmd.append("--generate-uvs")

        if center_model:
            cmd.append("--center-model")

        # Run conversion
        print(f"  Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Print IfcConvert output
            if result.stdout:
                print("  IfcConvert output:")
                for line in result.stdout.strip().split("\n"):
                    print(f"    {line}")

            print(f"✓ GLB export complete: {glb_path}")

            # Show file sizes
            if glb_path.exists():
                glb_mb = glb_path.stat().st_size / (1024 * 1024)
                print(f"  GLB size: {glb_mb:.1f} MB")

        except subprocess.CalledProcessError as e:
            print("✗ IfcConvert failed:")
            print(f"  Error code: {e.returncode}")
            if e.stdout:
                print(f"  stdout: {e.stdout}")
            if e.stderr:
                print(f"  stderr: {e.stderr}")
            raise


def convert_ifc_to_glb(
    ifc_path: Path,
    glb_path: Path,
    use_world_coords: bool = True,
    generate_uvs: bool = True,
    center_model: bool = False,
) -> None:
    """Convenience function to convert IFC to GLB.

    Args:
        ifc_path: Input IFC file
        glb_path: Output GLB file
        use_world_coords: Use world coordinates (preserves geo-location)
        generate_uvs: Generate UV coordinates for textures
        center_model: Center model at origin (useful for web viewers)

    Example:
        >>> from giskit.exporters.glb_exporter import convert_ifc_to_glb
        >>> convert_ifc_to_glb('input.ifc', 'output.glb')
    """
    exporter = GLBExporter()
    exporter.ifc_to_glb(
        ifc_path,
        glb_path,
        use_world_coords=use_world_coords,
        generate_uvs=generate_uvs,
        center_model=center_model,
    )


def check_ifcconvert_installation() -> dict:
    """Check IfcConvert installation and return info.

    Returns:
        Dict with 'available' (bool), 'path' (str or None), 'version' (str or None),
        and 'platform' (str)
    """
    exporter = GLBExporter()

    info = {
        "available": exporter.is_available(),
        "path": exporter.ifcconvert_path,
        "version": None,
        "platform": f"{platform_module.system()} {platform_module.machine()}",
        "binary_name": get_binary_name(),
    }

    if exporter.is_available() and exporter.ifcconvert_path:
        try:
            result = subprocess.run(
                [exporter.ifcconvert_path, "--version"], capture_output=True, text=True, timeout=5
            )
            info["version"] = result.stdout.strip() or result.stderr.strip()
        except Exception:
            pass

    return info
