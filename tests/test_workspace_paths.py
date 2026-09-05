from pathlib import Path

from crucible_workspace.paths import (
    WORKSPACE_DIR_ENV_VAR,
    get_runtime_data_dir,
    get_workflows_dir,
    get_workspace_dir,
)


def test_get_workspace_dir_uses_env_override_when_set(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(WORKSPACE_DIR_ENV_VAR, str(tmp_path))

    assert get_workspace_dir() == tmp_path


def test_get_workspace_dir_falls_back_to_platformdirs_when_unset(monkeypatch) -> None:
    monkeypatch.delenv(WORKSPACE_DIR_ENV_VAR, raising=False)

    workspace_dir = get_workspace_dir()

    assert workspace_dir.name == "Crucible"


def test_get_workflows_dir_is_nested_under_workspace_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(WORKSPACE_DIR_ENV_VAR, str(tmp_path))

    assert get_workflows_dir() == tmp_path / "workflows"


def test_get_runtime_data_dir_is_nested_under_workspace_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(WORKSPACE_DIR_ENV_VAR, str(tmp_path))

    assert get_runtime_data_dir() == tmp_path / "runtime"
