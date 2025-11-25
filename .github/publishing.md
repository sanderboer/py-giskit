# GitHub Actions Workflows

Dit project gebruikt GitHub Actions voor Continuous Integration en Deployment.

## Workflows

### 1. Tests (`tests.yml`)

**Trigger**: Push naar `main`/`develop`, Pull Requests

**Doel**: Automatisch testen op meerdere platforms en Python versies

**Matrix**:
- **OS**: Ubuntu, macOS, Windows
- **Python**: 3.10, 3.11, 3.12

**Stappen**:
1. Code checkout
2. Python en Poetry installatie
3. Dependencies installeren (met caching)
4. Tests uitvoeren met coverage
5. Upload coverage naar Codecov (alleen Ubuntu/Python 3.10)
6. Ruff linting
7. Black formatting check

### 2. Publish to PyPI (`publish-pypi.yml`)

**Trigger**:
- GitHub Release published
- Manual trigger (workflow_dispatch)

**Doel**: Package bouwen en publiceren naar PyPI

**Jobs**:

#### Build
1. Code checkout
2. Poetry installatie
3. Dependencies en project installatie
4. Tests uitvoeren
5. Ruff linting
6. Package bouwen
7. Artifacts uploaden

#### Publish to PyPI
- **Condition**: Alleen bij GitHub Release
- **Environment**: `pypi`
- **Auth**: Trusted Publishing (OIDC)
- **Target**: https://pypi.org

#### Publish to TestPyPI
- **Condition**: Alleen bij manual trigger
- **Environment**: `testpypi`
- **Auth**: Trusted Publishing (OIDC)
- **Target**: https://test.pypi.org

## Setup Vereisten

### GitHub Secrets

**GEEN SECRETS NODIG!** Dit project gebruikt Trusted Publishing via OIDC.

### GitHub Environments

Maak de volgende environments in GitHub Settings:

#### `pypi`
- **URL**: `https://pypi.org/p/giskit`
- **Protection**:
  - Required reviewers (aanbevolen)
  - Deployment branches: `main` only

#### `testpypi`
- **URL**: `https://test.pypi.org/p/giskit`
- **Protection**: Geen (voor testen)

### PyPI Trusted Publisher Setup

Zie [GITHUB_PYPI_SETUP.md](../GITHUB_PYPI_SETUP.md) voor gedetailleerde instructies.

**Snel overzicht**:

1. Ga naar https://pypi.org/manage/account/publishing/
2. Add new publisher:
   - Owner: `a190`
   - Repository: `giskit`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi`

## Gebruik

### Tests Runnen

Tests worden automatisch uitgevoerd bij:
- Push naar `main` of `develop`
- Elke Pull Request

### Publiceren naar TestPyPI

1. Ga naar **Actions** tab
2. Selecteer "Publish to PyPI"
3. **Run workflow** (manual trigger)
4. Wacht op build + test
5. Package wordt gepubliceerd naar TestPyPI

### Publiceren naar PyPI

1. Update versie in `pyproject.toml` en `giskit/__init__.py`
2. Update `CHANGELOG.md`
3. Commit en push naar `main`
4. Maak een GitHub Release:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```
5. Of via GitHub UI: Releases → Draft new release
6. Workflow wordt automatisch getriggerd
7. Package wordt gepubliceerd naar PyPI

## Troubleshooting

### Workflow fails met "permission denied"

Zorg dat `permissions: id-token: write` aanwezig is in de workflow.

### "Invalid or non-existent authentication"

1. Check PyPI Trusted Publisher settings
2. Verify environment naam klopt
3. Check repository naam en owner

### Tests falen

Lokaal testen:
```bash
poetry install
poetry run pytest tests/unit/ -v
poetry run ruff check .
```

### Build fails

Check:
- `pyproject.toml` syntax
- Alle dependencies zijn gespecificeerd
- `poetry.lock` is up-to-date

## Badges

Voeg toe aan README.md:

```markdown
[![Tests](https://github.com/a190/giskit/actions/workflows/tests.yml/badge.svg)](https://github.com/a190/giskit/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/giskit)](https://pypi.org/project/giskit/)
[![Python](https://img.shields.io/pypi/pyversions/giskit)](https://pypi.org/project/giskit/)
```

## Meer Info

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPA Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [Trusted Publishing Guide](../GITHUB_PYPI_SETUP.md)
