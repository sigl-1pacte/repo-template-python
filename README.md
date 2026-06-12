# {{PROJECT_NAME}}

Generated from **repo-template-python**. The provisioning service replaces every
`{{PLACEHOLDER}}` before pushing the stamped copy to the user's repository.

---

## Layout

```
.
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI application (entry point)
├── k8s/
│   ├── namespace.yaml   # Kubernetes Namespace
│   ├── deployment.yaml  # Kubernetes Deployment (1 replica, liveness/readiness on /health)
│   └── service.yaml     # Kubernetes Service (ClusterIP, port 80 → 8000)
├── .dockerignore
├── Dockerfile           # Multi-step: copies uv from ghcr.io/astral-sh/uv, installs deps, runs uvicorn
└── pyproject.toml       # uv-managed project metadata and dependencies
```

---

## Placeholder variables

| Variable | Description | Example |
|---|---|---|
| `{{PROJECT_NAME}}` | Slug used as the Kubernetes resource name and image name | `my-service` |
| `{{NAMESPACE}}` | Kubernetes namespace to deploy into | `team-alpha` |
| `{{IMAGE_REGISTRY}}` | Container registry host (no trailing slash) | `registry.example.com` |
| `{{IMAGE_TAG}}` | Docker image tag, typically a short Git SHA | `a1b2c3d` |

The provisioning service performs a simple find-and-replace across all files before
committing the result to the user's repository.

---

## Local development

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Run the app
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest
```

The app exposes a single endpoint:

```
GET /health  →  {"status": "ok"}
```

---

## Quality checks

```bash
# Install locked dependencies, including CI tooling
uv sync --locked --dev

# Run the same checks as GitHub Actions
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run bandit -r . -x ./tests,./.venv,./venv
uv run pip-audit
```

Bandit and pip-audit run as non-blocking steps in CI while the template is still
generic. They can be made blocking later by removing `continue-on-error: true`
from the workflow.

---

## Building and pushing the image

```bash
IMAGE=registry.example.com/my-service:$(git rev-parse --short HEAD)

docker build -t "$IMAGE" .
docker push "$IMAGE"
```

Commit `uv.lock` to the repository after the first `uv sync` so subsequent builds
are fully reproducible (`uv sync --frozen` is the recommended production flag).

---

## Deploying to Kubernetes

After substituting placeholders, apply the manifests in order:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Or apply the whole directory (namespace must already exist):

```bash
kubectl apply -f k8s/
```

ArgoCD points at the `k8s/` directory and syncs automatically on every push.
