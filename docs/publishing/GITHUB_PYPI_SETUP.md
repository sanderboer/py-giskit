# GitHub & PyPI Trusted Publishing Setup

## 📋 Overzicht

PyPI ondersteunt **Trusted Publishing** via OpenID Connect (OIDC). Dit is veiliger dan API tokens omdat:
- ✅ Geen lange-termijn credentials nodig
- ✅ Automatische authenticatie via GitHub Actions
- ✅ Geen secrets die verlopen of geroteerd moeten worden
- ✅ Betere audit trail

## 🔧 Setup Stappen

### Stap 1: PyPI Account Voorbereiden

1. Ga naar [PyPI](https://pypi.org) (of [Test PyPI](https://test.pypi.org))
2. Log in of maak een account aan
3. **BELANGRIJK**: De eerste keer moet je handmatig uploaden met een API token om het project te claimen

#### Eerste Handmatige Upload (Eenmalig)

```bash
# Maak een API token aan
# https://pypi.org/manage/account/token/
# Scope: "Entire account" voor eerste upload

# Upload naar PyPI
poetry build
twine upload dist/* --username __token__ --password <your-api-token>

# Upload naar Test PyPI (optioneel)
twine upload --repository testpypi dist/* \
  --username __token__ \
  --password <your-test-pypi-token>
```

### Stap 2: Trusted Publishing Configureren op PyPI

#### Voor NIEUWE projecten (nog niet op PyPI):

1. Ga naar [PyPI Publishing](https://pypi.org/manage/account/publishing/)
2. Klik "Add a new pending publisher"
3. Vul in:
   - **PyPI Project Name: `pygiskit`
   - **Owner**: `a190` (je GitHub username/org)
   - **Repository name**: `giskit`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi` (optioneel maar aanbevolen)
4. Klik "Add"

#### Voor BESTAANDE projecten (al op PyPI):

1. Ga naar je project: https://pypi.org/manage/project/pygiskit/settings/
2. Scroll naar "Publishing"
3. Klik "Add a new publisher"
4. Vul in:
   - **Owner**: `a190`
   - **Repository**: `giskit`
   - **Workflow**: `publish-pypi.yml`
   - **Environment**: `pypi`
5. Klik "Add"

### Stap 3: GitHub Environment Instellen (Aanbevolen)

Environments bieden extra beveiliging en controle.

1. Ga naar je GitHub repo: `https://github.com/a190/giskit`
2. Ga naar **Settings** → **Environments**
3. Klik **New environment**
4. Maak twee environments:

#### PyPI Environment

- **Name**: `pypi`
- **Environment protection rules** (optioneel):
  - ✅ Required reviewers: voeg jezelf toe
  - ✅ Wait timer: 0 minuten (of meer voor extra safety)
  - ✅ Deployment branches: Alleen `main` branch
- **Environment secrets**: geen nodig met Trusted Publishing!

#### TestPyPI Environment (Optioneel)

- **Name**: `testpypi`
- Geen protection rules nodig (voor testen)

### Stap 4: Workflow Verificatie

De workflow in `.github/workflows/publish-pypi.yml` heeft:

```yaml
permissions:
  id-token: write  # CRITICAL: Dit geeft toegang tot OIDC token

environment:
  name: pypi
  url: https://pypi.org/p/pygiskit
```

### Stap 5: Test de Workflow

#### Optie A: Handmatig Triggeren (Aanbevolen voor eerste test)

1. Ga naar **Actions** tab in GitHub
2. Selecteer "Publish to PyPI" workflow
3. Klik **Run workflow**
4. Selecteer branch `main`
5. Dit triggert upload naar **TestPyPI** (workflow_dispatch)

#### Optie B: Via GitHub Release

1. Ga naar **Releases** in GitHub
2. Klik **Draft a new release**
3. Vul in:
   - **Tag**: `v0.1.0` (nieuw)
   - **Target**: `main`
   - **Release title**: `v0.1.0`
   - **Description**: Kopieer van CHANGELOG.md
4. Klik **Publish release**
5. Dit triggert automatisch upload naar **PyPI**

## 🔍 Hoe Werkt Trusted Publishing?

```
┌─────────────────┐
│  GitHub Actions │
│                 │
│  1. Workflow    │──┐
│     triggered   │  │
└─────────────────┘  │
                     │
                     ▼
         ┌───────────────────┐
         │  GitHub OIDC      │
         │  Provider         │
         │                   │
         │  2. Issues token  │
         │     with claims:  │
         │     - repo        │
         │     - workflow    │
         │     - environment │
         └───────────────────┘
                     │
                     ▼
         ┌───────────────────┐
         │  PyPI             │
         │                   │
         │  3. Validates:    │
         │     ✓ Repo match  │
         │     ✓ Workflow    │
         │     ✓ Environment │
         │                   │
         │  4. Allows upload │
         └───────────────────┘
```

## 📊 Voordelen vs Nadelen

### Trusted Publishing (OIDC)

✅ **Voordelen**:
- Geen secrets in GitHub
- Automatische rotatie
- Betere security
- Audit trail via GitHub

❌ **Nadelen**:
- Alleen via GitHub Actions
- Iets complexere setup
- Moet eerst project claimen

### API Tokens (Oude Methode)

✅ **Voordelen**:
- Simpeler voor één-keer uploads
- Werkt overal (lokaal, andere CI)

❌ **Nadelen**:
- Secrets moeten veilig opgeslagen
- Handmatige rotatie
- Security risk bij leak

## 🎯 Aanbevolen Workflow

1. **Development**: Werk op feature branches
2. **PR Review**: Maak PR naar `main`
3. **Tests**: Automatische tests via `.github/workflows/tests.yml`
4. **Merge**: Merge PR naar `main`
5. **Manual Test**: Trigger workflow handmatig → TestPyPI
6. **Verify**: Test installatie van TestPyPI
7. **Release**: Maak GitHub Release → Automatisch naar PyPI
8. **Verify**: Test installatie van PyPI

## 🔐 Security Best Practices

### ✅ DO

- Gebruik environments voor productie uploads
- Voeg required reviewers toe aan `pypi` environment
- Beperk deploy naar `main` branch only
- Test eerst op TestPyPI
- Gebruik semantic versioning

### ❌ DON'T

- Upload nooit direct naar PyPI zonder tests
- Gebruik geen `workflow_dispatch` voor productie
- Skip nooit code review voor releases
- Hergebruik nooit versie nummers

## 🐛 Troubleshooting

### "Error: Invalid or non-existent authentication information"

**Oplossing**:
1. Check of project bestaat op PyPI
2. Verify Trusted Publisher settings kloppen
3. Check environment naam in workflow = environment op PyPI

### "Error: This filename has already been used"

**Oplossing**:
- Bump versie nummer in `pyproject.toml`
- PyPI accepteert GEEN reuploads van dezelfde versie

### Workflow fails met "permission denied"

**Oplossing**:
```yaml
permissions:
  id-token: write  # <- Dit moet aanwezig zijn!
```

## 📚 Referenties

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC Docs](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [PyPA Publish Action](https://github.com/pypa/gh-action-pypi-publish)

## 🔄 GitLab Support

**Let op**: Trusted Publishing werkt momenteel **alleen met GitHub Actions**. Voor GitLab CI moet je nog steeds API tokens gebruiken:

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  script:
    - pip install poetry twine
    - poetry build
    - twine upload dist/* --username __token__ --password $PYPI_TOKEN
  only:
    - tags
  variables:
    PYPI_TOKEN: $PYPI_API_TOKEN  # Sla op in GitLab CI/CD Variables
```

PyPI werkt aan support voor meer platforms, maar momenteel is GitHub de enige ondersteunde.
