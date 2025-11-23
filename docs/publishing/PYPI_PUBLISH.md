# PyPI Publication Instructions for GISKit

This document describes how to publish GISKit to PyPI using GitHub Actions with Trusted Publishing (OIDC).

## Overview

GISKit is configured for automated publishing to PyPI via GitHub Actions. The workflow supports:
- **Automatic publishing** to PyPI when creating a GitHub Release
- **Manual publishing** to TestPyPI for testing
- **Trusted Publishing (OIDC)** - no API tokens needed!


## Prerequisites (One-Time Setup)

### 1. Configure PyPI Trusted Publishing

**For PyPI (production):**
1. Go to https://pypi.org/manage/account/publishing/
2. Add a "pending publisher" with these details:
   - PyPI Project Name: `giskit`
   - Owner: `sanderboer`
   - Repository name: `py-giskit`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`

**For TestPyPI (testing):**
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add the same pending publisher configuration
3. Environment name: `testpypi`

See `GITHUB_PYPI_SETUP.md` for detailed setup instructions.

### 2. Configure GitHub Environments

1. Go to https://github.com/sanderboer/py-giskit/settings/environments
2. Create two environments:

**Environment: `pypi`**
- Required reviewers: Add yourself (recommended for production safety)
- No other restrictions needed

**Environment: `testpypi`**
- No restrictions (for quick testing)

## Current Package Configuration

- **Package name:** `giskit`
- **Python support:** 3.10, 3.11, 3.12 (limited to <3.13 for ifcopenshell compatibility)
- **Current version:** `0.1.0-dev`
- **Optional extras:**
  - `giskit[ifc]` - Includes ifcopenshell for IFC export
  - `giskit[all]` - All optional dependencies

## Publishing Workflow

### Option 1: Publish to TestPyPI (Recommended First)


**Steps:**

1. **Ensure tests pass:**
   ```bash
   poetry run pytest tests/
   poetry run ruff check .
   poetry run ruff format --check .
   ```

2. **Trigger the manual workflow:**
   - Go to https://github.com/sanderboer/py-giskit/actions/workflows/publish-pypi.yml
   - Click "Run workflow"
   - Select branch: `main`
   - Click "Run workflow"

3. **Monitor the deployment:**
   - Check the Actions tab for progress
   - Package will be published to https://test.pypi.org/project/pygiskit/

4. **Test the installation:**
   ```bash
   # Create a test environment
   python -m venv test_env
   source test_env/bin/activate

   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     giskit

   # Test basic functionality
   giskit --version
   python -c "import giskit; print('GISKit imported successfully')"

   # Test with IFC extra
   pip install --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     giskit[ifc]
   ```

### Option 2: Publish to PyPI (Production)


**Steps:**

1. **Update version number:**
   ```bash
   # In pyproject.toml, change:
   version = "0.1.0-dev"  # to
   version = "0.1.0"      # or your target version
   ```

2. **Run final checks:**
   ```bash
   # Update lock file
   poetry lock --no-update

   # Run all tests
   poetry run pytest tests/

   # Check code quality
   poetry run ruff check .
   poetry run ruff format --check .
   ```

3. **Commit the version bump:**
   ```bash
   git add pyproject.toml poetry.lock
   git commit -m "Bump version to 0.1.0"
   git push origin main
   ```

4. **Create a GitHub Release:**
   - Go to https://github.com/sanderboer/py-giskit/releases
   - Click "Create a new release"
   - Click "Choose a tag" and create new tag: `v0.1.0`
   - Target: `main`
   - Release title: `v0.1.0`
   - Description: Add release notes (see template below)
   - Click "Publish release"

5. **Automated publishing:**
   - GitHub Actions will automatically trigger
   - The `pypi` environment requires approval (check your email)
   - Approve the deployment
   - Monitor at https://github.com/sanderboer/py-giskit/actions

6. **Verify publication:**
   ```bash
   # Test installation from PyPI
   pip install pygiskit
   giskit --version

   # Test with IFC support
   pip install pygiskit[ifc]
   ```

**Release Notes Template:**
```markdown
## GISKit v0.1.0

### Features
- Recipe-driven spatial data downloader for any location
- Support for PDOK WFS, OGC API Features, WMTS protocols
- OpenStreetMap Overpass API integration
- Export to GeoPackage, GeoJSON, Shapefile, GML, CityJSON
- Optional IFC export support (via `pip install pygiskit[ifc]`)

### Installation
```bash
pip install pygiskit

# With IFC support
pip install pygiskit[ifc]
```

### Documentation
- GitHub: https://github.com/sanderboer/py-giskit
- Issues: https://github.com/sanderboer/py-giskit/issues
```


## Pre-Release Checklist

Before publishing, ensure:

- [ ] All tests pass: `poetry run pytest tests/`
- [ ] Code is formatted: `poetry run ruff format --check .`
- [ ] No linting errors: `poetry run ruff check .`
- [ ] Version number updated in `pyproject.toml`
- [ ] `poetry.lock` is up to date
- [ ] README.md is accurate and complete
- [ ] LICENSE file is present
- [ ] For PyPI: Tested on TestPyPI first
- [ ] Git changes committed and pushed
- [ ] Release notes prepared

## Package Information

**Supported Features:**
- Python 3.10, 3.11, 3.12
- Core dependencies: geopandas, shapely, httpx, pydantic, typer
- Optional: ifcopenshell (Python <3.13 only)
- CLI tool: `giskit`

**Package URLs:**
- PyPI: https://pypi.org/project/pygiskit/
- TestPyPI: https://test.pypi.org/project/pygiskit/
- Repository: https://github.com/sanderboer/py-giskit

## Manual Publishing (Fallback)

If GitHub Actions are unavailable, you can publish manually:


```bash
# Install publishing tools
pip install twine

# Build the package
poetry build

# Check the build
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

**Note:** With Trusted Publishing configured, you'll need PyPI API tokens for manual uploads.
Create tokens at:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/


## Troubleshooting

### "File already exists" error
PyPI doesn't allow re-uploading the same version. Increment the version number in `pyproject.toml` and rebuild.

### Missing dependencies after install
Verify all dependencies are correctly listed in `pyproject.toml` under `[tool.poetry.dependencies]`.

### Import errors after installation
Check that the package structure is correct and config files (YAML) are included in the build.

### GitHub Actions workflow fails
1. Check that Trusted Publishing is configured on PyPI/TestPyPI
2. Verify GitHub environments (`pypi`, `testpypi`) are created
3. Check workflow logs for specific errors
4. Ensure `poetry.lock` is committed

### Python version compatibility issues
GISKit requires Python 3.10-3.12 (not 3.13+) due to ifcopenshell dependency.
Users on Python 3.13+ should use a compatible Python version.

## More Information

- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [GitHub Actions Publishing](https://docs.github.com/en/actions/publishing-packages/publishing-packages-with-github-actions)
- [PyPI Help](https://pypi.org/help/)
