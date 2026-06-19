from pathlib import Path

import pytest

from generate import ci_orchestrator, dependabot, load_config, supported_apps


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "monorepo.config.yml"
    path.write_text(content)
    return path


def test_load_config_keeps_node_but_supported_apps_skips_it(tmp_path, capsys):
    config_path = write_config(
        tmp_path,
        """project: my-project

apps:
  - name: app1
    path: apps/app1
    language: python
    python_version: "3.12"

  - name: app2
    path: apps/app2
    language: node
    node_version: 20
    package_manager: pnpm
""",
    )

    apps = load_config(config_path)
    apps_to_generate = supported_apps(apps)

    assert [app.name for app in apps] == ["app1", "app2"]
    assert [app.name for app in apps_to_generate] == ["app1"]
    assert (
        "Warning: language 'node' is not implemented yet. Skipping app 'app2'."
        in capsys.readouterr().out
    )


def test_orchestrator_references_only_supported_python_apps(tmp_path):
    config_path = write_config(
        tmp_path,
        """apps:
  - name: app1
    path: apps/app1
    language: python

  - name: app2
    path: apps/app2
    language: node
""",
    )

    apps_to_generate = supported_apps(load_config(config_path))
    workflow = ci_orchestrator(apps_to_generate)

    assert "app1:" in workflow
    assert "ci-app1.yml" in workflow
    assert "apps/app1/**" in workflow
    assert "app2:" not in workflow
    assert "ci-app2.yml" not in workflow
    assert "apps/app2/**" not in workflow


def test_dependabot_references_only_supported_python_apps(tmp_path):
    config_path = write_config(
        tmp_path,
        """apps:
  - name: app1
    path: apps/app1
    language: python

  - name: app2
    path: apps/app2
    language: node
""",
    )

    apps_to_generate = supported_apps(load_config(config_path))
    content = dependabot(apps_to_generate)

    assert 'package-ecosystem: "uv"' in content
    assert 'directory: "/apps/app1"' in content
    assert "/apps/app2" not in content
    assert "npm" not in content


def test_load_config_rejects_duplicate_app_names(tmp_path):
    config_path = write_config(
        tmp_path,
        """apps:
  - name: app1
    path: apps/app1
    language: python

  - name: app1
    path: apps/other
    language: python
""",
    )

    with pytest.raises(ValueError, match="Duplicate app name: app1"):
        load_config(config_path)
