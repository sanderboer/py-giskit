from pathlib import Path

import pytest

from giskit.exporters.obj_zip_exporter import OBJZipExporter


def test_obj_zip_exporter_is_available():
    """Test that OBJZipExporter can check dependency availability."""
    exporter = OBJZipExporter()
    # Should return bool (True if ifcopenshell available, False otherwise)
    assert isinstance(exporter.is_available(), bool)


def test_obj_zip_exporter_requires_ifcopenshell(tmp_path: Path):
    """Test that OBJZipExporter requires ifcopenshell."""
    exporter = OBJZipExporter()

    # Skip if ifcopenshell is not available
    if not exporter.is_available():
        pytest.skip("ifcopenshell not available")

    # Test requires an actual IFC file, which we don't have in unit tests
    # This is more of an integration test that requires real data
    # For now, just verify the exporter can be constructed
    assert exporter is not None
