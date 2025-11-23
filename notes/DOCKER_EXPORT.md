# Docker Export Setup

This directory contains a Docker setup for running GISKit IFC/GLB exports in a containerized environment.

## Quick Start

### 1. Build the Docker Image

```bash
cd giskit/
docker build -f Dockerfile.export -t giskit-export .
```

### 2. Run Export Pipeline

```bash
# Prepare your data
mkdir -p data/input data/output
# Copy your GeoPackage to data/input/

# Run complete pipeline (GeoPackage → IFC → GLB)
docker run -v $(pwd)/data:/data giskit-export \
    python /app/examples/export_pipeline.py \
    /data/input/your_file.gpkg \
    /data/output
```

## What's Included

The Docker image includes:
- Python 3.11
- GISKit with all dependencies
- IfcConvert (v0.8.4, Linux x86_64)
- SpatiaLite support
- Complete IFC and GLB export capabilities

## Usage Examples

### Export GeoPackage to IFC Only

```bash
docker run -v $(pwd)/data:/data giskit-export python -c "
from pathlib import Path
from giskit.exporters.ifc import IFCExporter

exporter = IFCExporter()
exporter.export(
    db_path=Path('/data/input.gpkg'),
    output_path=Path('/data/output.ifc'),
    project_name='My Project',
    site_name='My Site'
)
"
```

### Convert IFC to GLB Only

```bash
docker run -v $(pwd)/data:/data giskit-export python -c "
from pathlib import Path
from giskit.exporters.glb_exporter import convert_ifc_to_glb

convert_ifc_to_glb(
    ifc_path=Path('/data/input.ifc'),
    glb_path=Path('/data/output.glb')
)
"
```

### Batch Processing

```bash
# Create a custom batch script
cat > batch_export.py << 'EOF'
from pathlib import Path
from giskit.exporters.ifc import IFCExporter
from giskit.exporters.glb_exporter import convert_ifc_to_glb

input_dir = Path('/data/input')
output_dir = Path('/data/output')
output_dir.mkdir(exist_ok=True)

exporter = IFCExporter()

for gpkg_file in input_dir.glob('*.gpkg'):
    print(f"Processing {gpkg_file.name}...")

    ifc_path = output_dir / f"{gpkg_file.stem}.ifc"
    glb_path = output_dir / f"{gpkg_file.stem}.glb"

    # Export to IFC
    exporter.export(gpkg_file, ifc_path)

    # Convert to GLB
    convert_ifc_to_glb(ifc_path, glb_path)

    print(f"✓ {gpkg_file.name} complete")
EOF

# Run batch processing
docker run -v $(pwd)/data:/data -v $(pwd)/batch_export.py:/app/batch_export.py \
    giskit-export python /app/batch_export.py
```

## Verify Installation

```bash
docker run giskit-export python -c "
from giskit.exporters.glb_exporter import check_ifcconvert_installation
info = check_ifcconvert_installation()
print(f'IfcConvert available: {info[\"available\"]}')
print(f'Path: {info[\"path\"]}')
print(f'Version: {info[\"version\"]}')
print(f'Platform: {info[\"platform\"]}')
"
```

Expected output:
```
IfcConvert available: True
Path: /app/bin/IfcConvert
Version: IfcOpenShell IfcConvert 0.8.4-e8eb5e4
Platform: Linux x86_64
```

## Docker Compose Example

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  giskit-export:
    build:
      context: .
      dockerfile: Dockerfile.export
    image: giskit-export
    volumes:
      - ./data:/data
    command: python /app/examples/export_pipeline.py /data/input.gpkg /data/output
```

Run with:
```bash
docker-compose up
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Export to IFC/GLB

on:
  push:
    paths:
      - 'data/*.gpkg'

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -f giskit/Dockerfile.export -t giskit-export giskit/

      - name: Run export pipeline
        run: |
          docker run -v $(pwd)/data:/data giskit-export \
            python /app/examples/export_pipeline.py \
            /data/input.gpkg \
            /data/output

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: exports
          path: data/output/*
```

## Platform Notes

### Linux
- Default platform for Docker
- Uses IfcConvert Linux x86_64 binary
- Most efficient for CI/CD

### macOS / Windows
- Docker Desktop uses Linux VM internally
- Same Linux binary works across platforms
- Slightly slower due to VM overhead

### ARM (Apple Silicon)
- Docker Desktop uses emulation for x86_64
- Performance may vary
- For native ARM: Modify Dockerfile to use `linux-aarch64` binary (if available)

## Troubleshooting

### Container Size
The image is ~500MB due to:
- Python runtime (~150MB)
- GISKit dependencies (~200MB)
- IfcConvert binary (~103MB)

To reduce size, use multi-stage build (advanced).

### Volume Permissions
If you encounter permission errors:

```bash
# Run with user/group ID matching host
docker run -u $(id -u):$(id -g) -v $(pwd)/data:/data giskit-export ...
```

### Memory Limits
For large datasets, increase Docker memory:

```bash
docker run -m 4g -v $(pwd)/data:/data giskit-export ...
```

## Production Deployment

### Kubernetes Example

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: giskit-export
spec:
  template:
    spec:
      containers:
      - name: exporter
        image: giskit-export:latest
        command: ["python", "/app/examples/export_pipeline.py"]
        args: ["/data/input.gpkg", "/data/output"]
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: giskit-data
      restartPolicy: Never
```

### Cloud Run / AWS Lambda
The Docker image can be adapted for serverless platforms. See cloud provider documentation for specific requirements.

## Related Documentation

- [Export Guide](../EXPORT_GUIDE.md) - Complete export documentation
- [Dockerfile.export](Dockerfile.export) - Docker configuration
- [export_pipeline.py](examples/export_pipeline.py) - Sample pipeline script
