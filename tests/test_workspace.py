from pathlib import Path

import pytest

from crucible_workspace.exceptions import (
    InvalidWorkflowNameError,
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from crucible_workspace.store import WorkflowStore


def test_store_creates_workflows_directory(tmp_path: Path) -> None:
    workflows_dir = tmp_path / "workflows"

    WorkflowStore(workflows_dir=workflows_dir)

    assert workflows_dir.exists()
    assert workflows_dir.is_dir()


def test_create_workflow(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)
    content = "name: example\nsteps: []"

    workflow = store.create_workflow("example", content)

    assert workflow.name == "example"
    assert workflow.path == tmp_path / "example.yaml"
    assert workflow.path.read_text(encoding="utf-8") == content


def test_create_workflow_rejects_duplicate_name(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    store.create_workflow("example", "name: example\nsteps: []")

    with pytest.raises(WorkflowAlreadyExistsError):
        store.create_workflow("example", "name: example\nsteps: []")


def test_read_workflow(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)
    content = "name: example\nsteps: []"

    store.create_workflow("example", content)

    assert store.read_workflow("example") == content


def test_read_missing_workflow_raises_error(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    with pytest.raises(WorkflowNotFoundError):
        store.read_workflow("missing")


def test_update_workflow(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    store.create_workflow("example", "name: example\nsteps: []")

    updated_content = "name: example\nsteps:\n  - key: select_columns"
    workflow = store.update_workflow("example", updated_content)

    assert workflow.name == "example"
    assert workflow.path == tmp_path / "example.yaml"
    assert store.read_workflow("example") == updated_content


def test_update_missing_workflow_raises_error(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    with pytest.raises(WorkflowNotFoundError):
        store.update_workflow("missing", "name: missing\nsteps: []")


def test_delete_workflow(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    store.create_workflow("example", "name: example\nsteps: []")
    store.delete_workflow("example")

    assert not (tmp_path / "example.yaml").exists()


def test_delete_missing_workflow_raises_error(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    with pytest.raises(WorkflowNotFoundError):
        store.delete_workflow("missing")


def test_workflow_exists(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    assert store.workflow_exists("example") is False

    store.create_workflow("example", "name: example\nsteps: []")

    assert store.workflow_exists("example") is True


def test_list_workflows_returns_yaml_files_only(tmp_path: Path) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    store.create_workflow("b_workflow", "name: b_workflow\nsteps: []")
    store.create_workflow("a_workflow", "name: a_workflow\nsteps: []")

    (tmp_path / "ignore.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / "ignore.json").write_text("ignored", encoding="utf-8")

    workflows = store.list_workflows()

    assert [workflow.name for workflow in workflows] == [
        "a_workflow",
        "b_workflow",
    ]


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        "workflow/name",
        "workflow\\name",
        "../workflow",
        "workflow name",
        "workflow:name",
        "workflow*name",
    ],
)
def test_invalid_workflow_names_are_rejected(
    tmp_path: Path,
    invalid_name: str,
) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    with pytest.raises(InvalidWorkflowNameError):
        store.create_workflow(invalid_name, "name: invalid\nsteps: []")


@pytest.mark.parametrize(
    "valid_name",
    [
        "workflow",
        "workflow_1",
        "workflow-1",
        "workflow.1",
        "Workflow_ABC-123",
    ],
)
def test_valid_workflow_names_are_accepted(
    tmp_path: Path,
    valid_name: str,
) -> None:
    store = WorkflowStore(workflows_dir=tmp_path)

    workflow = store.create_workflow(valid_name, "name: valid\nsteps: []")

    assert workflow.name == valid_name
    assert workflow.path.exists()