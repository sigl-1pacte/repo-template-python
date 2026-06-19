from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "monorepo.config.yml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
DEPENDABOT_PATH = ROOT / ".github" / "dependabot.yml"


@dataclass(frozen=True)
class App:
    name: str
    path: str
    language: str
    options: dict[str, Any] = field(default_factory=dict)

    @property
    def workflow_name(self) -> str:
        return f"ci-{self.name}.yml"

    @property
    def python_version(self) -> str:
        return str(self.options.get("python_version", "3.12"))


WorkflowGenerator = Callable[[App], str]

LANGUAGE_GENERATORS: dict[str, WorkflowGenerator] = {
    "python": lambda app: ci_python(app),
    # "node": ci_node,  # TODO: implement later
    # "go": ci_go,  # TODO: implement later
    # "rust": ci_rust,  # TODO: implement later
    # "java": ci_java,  # TODO: implement later
}


def load_config(path: Path) -> list[App]:
    return load_config_data(yaml.safe_load(path.read_text()) or {})


def load_config_data(raw_config: Any) -> list[App]:
    if not isinstance(raw_config, dict):
        raise ValueError("monorepo.config.yml must contain a YAML object")

    raw_apps = raw_config.get("apps")
    if not isinstance(raw_apps, list) or not raw_apps:
        raise ValueError("monorepo.config.yml must contain a non-empty 'apps' list")

    apps = [
        parse_app(raw_app, index) for index, raw_app in enumerate(raw_apps, start=1)
    ]
    validate_apps(apps)
    return apps


def parse_app(raw_app: Any, index: int) -> App:
    if not isinstance(raw_app, dict):
        raise ValueError(f"App #{index} must be a YAML object")

    name = required_string(raw_app, "name", index)
    path = required_string(raw_app, "path", index).rstrip("/")
    language = required_string(raw_app, "language", index).lower()
    options = {key: value for key, value in raw_app.items() if key not in app_fields()}

    return App(name=name, path=path, language=language, options=options)


def app_fields() -> set[str]:
    return {"name", "path", "language"}


def required_string(raw_app: dict[str, Any], key: str, index: int) -> str:
    value = raw_app.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"App #{index} must define a non-empty string field '{key}'")
    return value.strip()


def validate_apps(apps: list[App]) -> None:
    names: set[str] = set()
    paths: set[str] = set()

    for app in apps:
        if app.name in names:
            raise ValueError(f"Duplicate app name: {app.name}")
        if app.path in paths:
            raise ValueError(f"Duplicate app path: {app.path}")
        names.add(app.name)
        paths.add(app.path)


def supported_apps(apps: list[App]) -> list[App]:
    supported = []
    for app in apps:
        if app.language not in LANGUAGE_GENERATORS:
            print(
                f"Warning: language '{app.language}' is not implemented yet. "
                f"Skipping app '{app.name}'."
            )
            continue
        supported.append(app)
    return supported


def ci_orchestrator(apps: list[App]) -> str:
    if not apps:
        return """name: Monorepo CI

on:
  pull_request:
  push:
    branches: [main, dev]

permissions:
  contents: read
  pull-requests: read

jobs:
  no-supported-apps:
    name: No supported apps
    runs-on: ubuntu-latest
    steps:
      - name: Nothing to run
        run: echo "No supported app CI has been generated."
"""

    outputs = "\n".join(
        f"      {app.name}: ${{{{ steps.filter.outputs.{app.name} }}}}" for app in apps
    )
    filters = "\n".join(filter_block(app) for app in apps)
    jobs = "\n\n".join(dispatch_job(app) for app in apps)

    return f"""name: Monorepo CI

on:
  pull_request:
  push:
    branches: [main, dev]

permissions:
  contents: write
  pull-requests: read

jobs:
  changes:
    name: Detect changed apps
    runs-on: ubuntu-latest
    outputs:
{outputs}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Detect changes
        id: filter
        uses: dorny/paths-filter@v4
        with:
          filters: |
{filters}

{jobs}
"""


def filter_block(app: App) -> str:
    return f"""            {app.name}:
              - '{app.path}/**'
              - '.github/workflows/ci.yml'
              - '.github/workflows/{app.workflow_name}'
              - 'monorepo.config.yml'
              - 'generate.py'"""


def dispatch_job(app: App) -> str:
    return f"""  {app.name}:
    name: {app.name}
    needs: changes
    if: ${{{{ needs.changes.outputs.{app.name} == 'true' }}}}
    uses: ./.github/workflows/{app.workflow_name}
    with:
      app-name: {app.name}
      app-path: {app.path}
      python-version: "{app.python_version}"
"""


def ci_python(app: App) -> str:
    return """name: Python App CI

on:
  workflow_call:
    inputs:
      app-name:
        required: true
        type: string
      app-path:
        required: true
        type: string
      python-version:
        required: false
        type: string
        default: "3.12"

permissions:
  contents: write

jobs:
  quality:
    name: Python quality
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: ${{ inputs.app-path }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Install Python
        run: uv python install ${{ inputs.python-version }}

      - name: Install dependencies
        run: uv sync --locked --dev

      - name: Ruff auto-fix
        run: uv run ruff check . --fix --unsafe-fixes

      - name: Ruff format
        run: uv run ruff format .

      - name: Commit Ruff fixes
        if: github.event_name == 'push'
        working-directory: ${{ github.workspace }}
        run: |
          if ! git diff --quiet; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add ${{ inputs.app-path }}
            git commit -m "style(${{ inputs.app-name }}): apply ruff fixes"
            git push
          fi

      - name: Ruff lint check
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Run tests if present
        run: |
          if [ -d tests ]; then
            uv run pytest
          else
            echo "No tests directory found for ${{ inputs.app-name }}"
          fi

      - name: Bandit security scan
        run: uv run bandit -r . -x ./tests,./.venv,./venv
        continue-on-error: true

      - name: Dependency audit
        run: uv run pip-audit
        continue-on-error: true
"""


def dependabot(apps: list[App]) -> str:
    entries = []
    for app in apps:
        if app.language == "python":
            entries.append(
                f'''  - package-ecosystem: "uv"
    directory: "/{app.path}"
    schedule:
      interval: "weekly"'''
            )

    if not entries:
        return "version: 2\nupdates: []\n"
    return "version: 2\nupdates:\n" + "\n\n".join(entries) + "\n"


def generate_ci_files(apps: list[App]) -> tuple[dict[str, str], list[str]]:
    files: dict[str, str] = {}
    warnings: list[str] = []
    apps_to_generate: list[App] = []

    for app in apps:
        if app.language not in LANGUAGE_GENERATORS:
            warnings.append(
                f"Warning: language '{app.language}' is not implemented yet. "
                f"Skipping app '{app.name}'."
            )
            continue
        apps_to_generate.append(app)

    files[".github/workflows/ci.yml"] = ci_orchestrator(apps_to_generate)
    for app in apps_to_generate:
        files[f".github/workflows/{app.workflow_name}"] = LANGUAGE_GENERATORS[
            app.language
        ](app)
    files[".github/dependabot.yml"] = dependabot(apps_to_generate)

    return files, warnings


def generate_ci_files_from_payload(raw_config: Any) -> tuple[dict[str, str], list[str]]:
    return generate_ci_files(load_config_data(raw_config))


def warn_obsolete_workflows(apps: list[App]) -> None:
    expected = {"ci.yml", *(app.workflow_name for app in apps)}
    existing = {
        path.name
        for path in WORKFLOWS_DIR.glob("ci-*.yml")
        if path.name not in expected
    }
    for workflow in sorted(existing):
        print(
            f"Warning: generated workflow '{workflow}' is no longer referenced. "
            "Remove it manually if it is obsolete."
        )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"generated {path.relative_to(ROOT)}")


def main() -> None:
    apps = load_config(CONFIG_PATH)
    files, warnings = generate_ci_files(apps)
    apps_to_generate = [app for app in apps if app.language in LANGUAGE_GENERATORS]

    for warning in warnings:
        print(warning)

    for relative_path, content in files.items():
        write(ROOT / relative_path, content)

    warn_obsolete_workflows(apps_to_generate)


if __name__ == "__main__":
    main()
