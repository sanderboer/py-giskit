# PyPI Publicatie Instructies voor GISKit

Dit document beschrijft hoe je GISKit publiceert op PyPI.

## Voorbereiding

### 1. Vereisten

```bash
# Installeer publicatie tools
pip install twine

# Zorg dat je een PyPI account hebt
# https://pypi.org/account/register/

# Maak een API token aan
# https://pypi.org/manage/account/token/
```

### 2. Test de build

```bash
# Maak een nieuwe build
poetry build

# Check de build
twine check dist/*
```

## Publicatie naar Test PyPI (Aanbevolen eerst)

### 1. Upload naar Test PyPI

```bash
# Upload naar test.pypi.org
twine upload --repository testpypi dist/*

# Of met API token
twine upload --repository testpypi dist/* \
  --username __token__ \
  --password <your-test-pypi-token>
```

### 2. Test de installatie

```bash
# Maak een nieuwe virtual environment
python -m venv test_env
source test_env/bin/activate  # of test_env\Scripts\activate op Windows

# Installeer van Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  giskit

# Test het package
giskit --version
python -c "import giskit; print(giskit.__version__)"
```

## Publicatie naar PyPI (Productie)

### 1. Update versie nummer

```bash
# In pyproject.toml, verander:
version = "0.1.0-dev"  # naar
version = "0.1.0"      # of een specifieke versie

# Update ook __version__ in giskit/__init__.py
```

### 2. Maak een nieuwe build

```bash
# Clean oude builds
rm -rf dist/

# Nieuwe build
poetry build

# Check opnieuw
twine check dist/*
```

### 3. Upload naar PyPI

```bash
# Upload naar pypi.org
twine upload dist/*

# Of met API token
twine upload dist/* \
  --username __token__ \
  --password <your-pypi-token>
```

### 4. Verificatie

```bash
# Test installatie
pip install giskit

# Met IFC support
pip install giskit[ifc]

# Check versie
giskit --version
```

## Git Tags en Releases

### 1. Maak een git tag

```bash
# Tag de release
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push de tag
git push origin v0.1.0
```

### 2. Maak een GitHub Release

1. Ga naar https://github.com/a190/giskit/releases
2. Klik "Create a new release"
3. Selecteer de tag (v0.1.0)
4. Voeg release notes toe (kopieer van CHANGELOG.md)
5. Upload de dist/ bestanden (optioneel)
6. Publiceer

## Configuratie Bestanden

### ~/.pypirc (Optioneel)

Maak dit bestand voor gemakkelijkere uploads:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-pypi-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-test-pypi-token>
```

Dan kun je uploaden met:

```bash
twine upload dist/*  # Gebruikt automatisch [pypi] config
twine upload --repository testpypi dist/*  # Voor test
```

## Checklist voor Publicatie

- [ ] Alle tests slagen (`pytest`)
- [ ] Ruff linting is schoon (`ruff check .`)
- [ ] Versie nummer is updated in pyproject.toml en __init__.py
- [ ] CHANGELOG.md is updated
- [ ] README.md is accuraat
- [ ] LICENSE bestand is aanwezig
- [ ] Build is successful (`poetry build`)
- [ ] Twine check passed (`twine check dist/*`)
- [ ] Getest op Test PyPI
- [ ] Git commit en tag gemaakt
- [ ] Upload naar PyPI
- [ ] GitHub release gemaakt
- [ ] Installatie getest

## Automatische Publicatie (Optioneel)

Je kunt GitHub Actions gebruiken voor automatische publicatie:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install poetry
        run: pip install poetry
      - name: Build
        run: poetry build
      - name: Publish
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          pip install twine
          twine upload dist/*
```

## Troubleshooting

### Upload faalt met "File already exists"

PyPI staat geen re-uploads toe van dezelfde versie. Bump het versie nummer en rebuild.

### Missing dependencies in install

Check of alle dependencies correct zijn in `pyproject.toml` en dat `MANIFEST.in` alle benodigde bestanden include.

### Import errors na installatie

Zorg dat de package structuur correct is en dat config bestanden worden meegenomen in de build.

## Meer Informatie

- [Python Packaging Guide](https://packaging.python.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PyPI Help](https://pypi.org/help/)
