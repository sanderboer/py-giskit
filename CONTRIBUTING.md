# Contributing to py-giskit

Bedankt voor je interesse om bij te dragen aan py-giskit! Dit document helpt je om snel aan de slag te gaan.

## 🚀 Quick Start

### 1. Fork en Clone

```bash
git clone https://github.com/YOUR_USERNAME/py-giskit.git
cd py-giskit
```

### 2. Development Environment Setup

```bash
# Installeer poetry (als je het nog niet hebt)
curl -sSL https://install.python-poetry.org | python3 -

# Installeer dependencies
poetry install

# Activeer virtual environment
poetry shell

# Installeer pre-commit hooks (belangrijk!)
pre-commit install
```

### 3. Maak een feature branch

```bash
git checkout -b feature/jouw-feature-naam
```

## ✅ Pre-commit Hooks (Verplicht)

**Waarom verplicht?** Voorkomt dat linting errors en test failures de CI/CD pipeline laten falen.

### Wat wordt er automatisch gecontroleerd bij elke commit?

- ✨ **Ruff formatter** - Consistente code formatting (draait eerst)
- 🔍 **Ruff linter** - Auto-fix van code issues met `--exit-non-zero-on-fix`
- 🧪 **Unit tests** - Alleen `tests/unit/` (snel, geen externe APIs)
- 📝 **File checks** - Trailing whitespace, end-of-file, YAML/TOML syntax

**Let op:** De linter faalt als er auto-fixes worden toegepast. Dit zorgt ervoor dat je de fixes kunt reviewen voordat je committed.

### Installatie

```bash
pre-commit install
```

### Gebruik

De hooks draaien **automatisch** bij `git commit`. Als een hook faalt:

- **Ruff/formatting**: Automatisch gefixt → `git add .` en commit opnieuw
- **Tests**: Fix de test eerst, commit daarna
- **Trailing whitespace**: Automatisch gefixt → `git add .` en commit opnieuw

### Handmatig alle hooks draaien

```bash
pre-commit run --all-files
```

### Hooks overslaan (niet aanbevolen)

```bash
git commit --no-verify -m "WIP: werk in uitvoering"
```

⚠️ **Let op**: CI draait dezelfde checks, dus een failing commit blokkeert je PR alsnog.

## 🧪 Tests Draaien

### Unit tests (snel, lokaal)

```bash
poetry run pytest tests/unit/ -v
```

### Integration tests (langzaam, externe APIs)

```bash
poetry run pytest tests/integration/ -v
```

### Alle tests

```bash
poetry run pytest -v
```

### Coverage report

```bash
poetry run pytest --cov=giskit --cov-report=html
open htmlcov/index.html
```

## 📋 Code Style

We gebruiken **Ruff** voor linting en formatting (pre-commit hooks zorgen hier automatisch voor).

### Handmatig linting

```bash
poetry run ruff check .
poetry run ruff check . --fix  # Auto-fix waar mogelijk
```

### Handmatig formatting

```bash
poetry run ruff format .
```

## 🔄 Pull Request Workflow

1. **Maak je wijzigingen** in een feature branch
2. **Voeg tests toe** voor nieuwe functionaliteit
3. **Run tests lokaal**: `poetry run pytest tests/unit/`
4. **Commit je wijzigingen** (pre-commit hooks runnen automatisch)
5. **Push naar je fork**: `git push origin feature/jouw-feature-naam`
6. **Open een Pull Request** op GitHub
7. **Wacht op CI/CD** - Alle checks moeten groen zijn
8. **Reageer op review feedback**

## 📁 Project Structuur

```
py-giskit/
├── giskit/              # Main package
│   ├── cli/            # CLI commands (typer)
│   ├── core/           # Core business logic
│   ├── protocols/      # Protocol implementations (OGC, OSM)
│   ├── providers/      # Data providers (PDOK, etc.)
│   ├── exporters/      # Export formats (IFC, GLB)
│   ├── config/         # Configuration schemas
│   └── indexer/        # Monitoring & quirks
├── tests/
│   ├── unit/           # Unit tests (fast, mocked)
│   └── integration/    # Integration tests (slow, real APIs)
├── recipes/            # Example recipe files
└── docs/               # Documentation
```

## 🐛 Bug Reports

Open een issue met:
- **Beschrijving**: Wat ging er mis?
- **Reproduceren**: Stappen om het probleem te reproduceren
- **Verwacht gedrag**: Wat had er moeten gebeuren?
- **Environment**: Python versie, OS, relevante dependencies

## 💡 Feature Requests

Open een issue met:
- **Use case**: Waarom is deze feature nuttig?
- **Voorstel**: Hoe zou het moeten werken?
- **Alternatieven**: Andere oplossingen overwogen?

## 📜 Commit Message Conventie

We volgen **conventional commits** voor duidelijke changelog generatie:

```
feat: add support for CityJSON export
fix: handle polygon holes in IFC export
docs: update CONTRIBUTING guide
test: add unit tests for temporal filtering
refactor: simplify quirks registry
```

Types:
- `feat`: Nieuwe feature
- `fix`: Bug fix
- `docs`: Documentatie
- `test`: Tests toevoegen/aanpassen
- `refactor`: Code refactoring (geen functionaliteitswijziging)
- `perf`: Performance verbetering
- `chore`: Build/tooling wijzigingen

## 🔒 Code Review Criteria

Je PR wordt beoordeeld op:

- ✅ Alle CI checks groen (linting, formatting, tests)
- ✅ Code coverage niet verminderd
- ✅ Nieuwe features hebben tests
- ✅ Documentatie bijgewerkt (indien nodig)
- ✅ Commit messages volgen conventie
- ✅ Code is leesbaar en goed gedocumenteerd

## 🚀 Releases & Publishing

**Voor maintainers:**

py-giskit gebruikt **automatische publishing** naar PyPI bij elke versie bump.

### Hoe een nieuwe versie releasen?

1. **Bump de versie** in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Was 0.1.0
   ```

2. **Commit en push naar main**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

3. **Automatische workflow triggert**:
   - ✅ Detecteert versie change
   - ✅ Draait pre-commit checks (linting, formatting, unit tests)
   - ✅ Bouwt package met poetry
   - ✅ Publiceert naar PyPI
   - ✅ Maakt automatisch een GitHub release met tag `v0.2.0`

**Dat's alles!** Binnen enkele minuten is de nieuwe versie live op PyPI.

### Versie Nummering

Volg [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (bijv. `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: Nieuwe features (backward compatible)
- **PATCH**: Bug fixes

## 🆘 Hulp Nodig?

- **GitHub Issues**: Voor bugs en feature requests
- **Discussions**: Voor vragen en ideeën
- **Email**: info@a190.nl

## 📄 Licentie

Door bij te dragen ga je akkoord dat je bijdragen gelicenseerd worden onder de MIT License.

---

**Bedankt voor je bijdrage! 🎉**
