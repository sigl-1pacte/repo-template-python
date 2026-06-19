# Documentation CI Monorepo

Cette CI est faite pour un monorepo: un seul repository GitHub, plusieurs apps,
et une app par sous-dossier. L'architecture est prevue pour plusieurs langages
par app, mais l'implementation actuelle genere uniquement les workflows Python.

Exemple cible:

```text
apps/
  api/              # Python
  front-office/     # futur Node/TS
  my-go-service/    # futur Go
packages/
  ui/
  types/
```

## Principe

GitHub impose que les workflows soient dans:

```text
.github/workflows/
```

On ne peut pas mettre des workflows dans des sous-dossiers par app. La solution
retenue est donc:

- un orchestrateur global: `.github/workflows/ci.yml`;
- un workflow reusable par app: `.github/workflows/ci-api.yml`;
- une config source: `monorepo.config.yml`;
- un generateur: `generate.py`;
- un Dependabot genere: `.github/dependabot.yml`.

Les langages futurs comme Node.js, Go, Rust et Java peuvent deja apparaitre dans
`monorepo.config.yml`. Ils seront ignores proprement tant que leur generateur
n'est pas implemente.

## Fichiers a modifier

La plateforme peut modifier la config directement, ou appeler l'API du service.
Dans les deux cas, la source fonctionnelle est:

```text
monorepo.config.yml
```

Puis elle relance:

```bash
python3 generate.py
```

Le generateur reecrit ensuite:

```text
.github/workflows/ci.yml
.github/workflows/ci-<app>.yml
.github/dependabot.yml
```

## API de generation

Le service expose des endpoints pour piloter la generation depuis une UI.

Lister les langages:

```http
GET /ci/languages
```

Reponse:

```json
{
  "supported": ["python"],
  "planned": ["node", "go", "rust", "java"]
}
```

Generer un preview sans ecrire dans le repo:

```http
POST /ci/generate/preview
Content-Type: application/json
```

Exemple de payload:

```json
{
  "project": "my-project",
  "apps": [
    {
      "name": "app1",
      "path": "apps/app1",
      "language": "python",
      "python_version": "3.12"
    },
    {
      "name": "app2",
      "path": "apps/app2",
      "language": "node",
      "node_version": 20,
      "package_manager": "pnpm"
    }
  ]
}
```

Exemple `curl`:

```bash
curl -X POST http://localhost:8000/ci/generate/preview \
  -H "Content-Type: application/json" \
  -d '{
    "project": "my-project",
    "apps": [
      {
        "name": "app1",
        "path": "apps/app1",
        "language": "python",
        "python_version": "3.12"
      },
      {
        "name": "app2",
        "path": "apps/app2",
        "language": "node",
        "node_version": 20,
        "package_manager": "pnpm"
      }
    ]
  }'
```

Reponse attendue:

```json
{
  "status": "preview",
  "warnings": [
    "Warning: language 'node' is not implemented yet. Skipping app 'app2'."
  ],
  "generated_files": [
    ".github/dependabot.yml",
    ".github/workflows/ci-app1.yml",
    ".github/workflows/ci.yml"
  ],
  "files": {
    ".github/workflows/ci.yml": "...",
    ".github/workflows/ci-app1.yml": "...",
    ".github/dependabot.yml": "..."
  }
}
```

Generer et ecrire les fichiers dans le repo:

```http
POST /ci/generate/apply
Content-Type: application/json
```

Cet endpoint ecrit les fichiers generes dans le workspace local. Il ne commit
pas et ne push pas vers GitHub. Pour une plateforme de production, il est
recommande de brancher cet endpoint sur une creation de branche et de pull
request, plutot qu'un commit direct sur `main`.

## Config actuelle

```yaml
apps:
  - name: api
    path: apps/api
    language: python
```

Cela veut dire:

- l'app s'appelle `api`;
- son code est dans `apps/api`;
- la CI a generer est une CI Python;
- Dependabot surveille les dependances `uv` dans `/apps/api`.

## Comment une CI specifique se lance

Le workflow `.github/workflows/ci.yml` se lance sur:

- `pull_request`;
- `push` vers `main`;
- `push` vers `dev`.

Il commence par le job `detect-changes`, qui utilise:

```yaml
dorny/paths-filter@v4
```

Pour l'app `api`, le filtre regarde:

```text
apps/api/**
.github/workflows/ci.yml
.github/workflows/ci-api.yml
monorepo.config.yml
generate.py
```

Si un fichier dans `apps/api/**` change, alors:

```text
needs.detect-changes.outputs.api == 'true'
```

et GitHub lance uniquement:

```text
.github/workflows/ci-api.yml
```

Si tu changes seulement `apps/front-office/**`, le job `api` ne se lancera pas,
quand `front-office` sera ajoute a la config.

Important: le workflow global se declenche toujours. Ce sont les jobs par app
qui sont executes ou ignores selon les chemins modifies.

## CI Python generee

Le workflow Python s'execute dans le dossier de l'app:

```yaml
working-directory: ${{ inputs.app-path }}
```

Pour `api`, cela donne:

```text
apps/api
```

Il attend donc ces fichiers dans `apps/api`:

```text
apps/api/pyproject.toml
apps/api/uv.lock
apps/api/tests/        # optionnel
```

Les etapes Python sont:

```bash
uv python install
uv sync --locked --dev
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run bandit -r . -x ./tests,./.venv,./venv
uv run pip-audit
```

`pytest` ne se lance que si le dossier `tests/` existe.

Bandit et pip-audit sont non bloquants au debut:

```yaml
continue-on-error: true
```

## Auto-fix Ruff

La CI Python corrige automatiquement le lint et le formatage:

```bash
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .
```

Puis elle commit les corrections sur la branche si GitHub Actions a le droit de
pousser.

Pre-requis GitHub:

```text
Settings -> Actions -> General -> Workflow permissions
Read and write permissions
```

Attention: une protection de branche peut bloquer le push automatique du bot.

## Ajouter une app Python depuis la plateforme

La plateforme doit:

1. creer le dossier de l'app, par exemple `apps/billing-api`;
2. creer un projet Python uv dans ce dossier;
3. ajouter les dependances dev CI dans `apps/billing-api/pyproject.toml`;
4. generer et committer `apps/billing-api/uv.lock`;
5. ajouter l'app dans `monorepo.config.yml`;
6. lancer `python3 generate.py`;
7. committer les workflows generes.

Exemple:

```yaml
apps:
  - name: api
    path: apps/api
    language: python
  - name: billing-api
    path: apps/billing-api
    language: python
```

Le generateur produira:

```text
.github/workflows/ci-api.yml
.github/workflows/ci-billing-api.yml
```

Et l'orchestrateur lancera seulement les jobs dont les chemins ont change.

## Ajouter un futur langage

Pour ajouter un langage, il faudra modifier `generate.py`:

1. ajouter le langage dans `LANGUAGE_GENERATORS`;
2. ajouter une fonction `ci_<language>(app)`;
3. brancher cette fonction dans le registre;
4. ajouter l'ecosysteme Dependabot correspondant dans `dependabot(apps)`.

Exemples futurs:

| Langage | Workflow futur | Dependabot |
| --- | --- | --- |
| Node/pnpm | `ci_node(app)` | `npm` |
| Go | `ci_go(app)` | `gomod` |
| Rust | `ci_rust(app)` | `cargo` |
| Java Maven | `ci_java(app)` | `maven` |
| Java Gradle | `ci_java(app)` | `gradle` |

## Dependances dev Python requises

Chaque app Python doit avoir au minimum:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.15.17",
    "bandit>=1.9.4",
    "pip-audit>=2.10.1",
]
```

Si l'app utilise FastAPI et `TestClient`, ajouter aussi `httpx`.

Apres modification:

```bash
cd apps/api
uv lock
uv sync --locked --dev
```

## Erreurs frequentes

### `Failed to spawn: ruff`

Ruff n'est pas installe dans l'environnement de l'app.

Verifier dans le dossier de l'app:

```bash
cd apps/api
uv sync --locked --dev
uv run ruff --version
```

Puis verifier que `pyproject.toml` et `uv.lock` sont bien committes.

### Le job d'une app ne se lance pas

Verifier:

- le `path` dans `monorepo.config.yml`;
- les filtres generes dans `.github/workflows/ci.yml`;
- que le push modifie bien un fichier sous ce path.

### Le bot ne peut pas commit les corrections Ruff

Verifier:

- `permissions.contents: write`;
- les permissions GitHub Actions du repo;
- les protections de branche.
