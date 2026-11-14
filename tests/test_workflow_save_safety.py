import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from crucible_workspace.exceptions import InvalidWorkflowContentError, WorkflowAlreadyExistsError
from crucible_workspace.store import WorkflowStore
from crucible_server.app import create_app
from crucible_server.dependencies import get_workflow_service
from crucible_server.services.workflows import WorkflowService


VALID = "name: example\nsteps: []\n"
INVALID_CONTENTS = [
    "name: example\nsteps: [",
    "name: example\nsteps:\n  - key: filter_rows\n    parameters:\n      condition:\n        operator: =\n",
    "steps: []\n",
    "name: example\nsteps: not-a-list\n",
]


@pytest.mark.parametrize("content", INVALID_CONTENTS)
def test_invalid_yaml_or_workflow_never_overwrites_existing_file(tmp_path, content):
    store = WorkflowStore(tmp_path)
    path = store.create_workflow("example", VALID).path
    before = path.read_bytes()
    with pytest.raises(InvalidWorkflowContentError):
        store.update_workflow("example", content)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("content", INVALID_CONTENTS)
def test_invalid_create_leaves_no_workflow_or_temporary_file(tmp_path, content):
    store = WorkflowStore(tmp_path)
    with pytest.raises(InvalidWorkflowContentError):
        store.create_workflow("example", content)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("operation", ["write", "replace"])
def test_failed_atomic_update_preserves_original_and_cleans_temporary_file(tmp_path, monkeypatch, operation):
    store = WorkflowStore(tmp_path)
    path = store.create_workflow("example", VALID).path

    def fail(*args):
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(os, "fsync" if operation == "write" else "replace", fail)
    with pytest.raises(OSError, match="disk failure"):
        store.update_workflow("example", "name: updated\nsteps: []\n")
    assert path.read_text() == VALID
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_update_preserves_file_mode_and_can_repair_an_invalid_existing_file(tmp_path):
    store = WorkflowStore(tmp_path)
    path = tmp_path / "example.yaml"
    path.write_text(INVALID_CONTENTS[1])
    path.chmod(0o640)
    mode = path.stat().st_mode
    store.update_workflow("example", VALID)
    assert path.read_text() == VALID
    assert path.stat().st_mode == mode


def test_concurrent_create_does_not_overwrite_the_other_file(tmp_path, monkeypatch):
    store = WorkflowStore(tmp_path)
    link = os.link

    def competing_create(source, destination):
        Path(destination).write_text("name: other\nsteps: []\n")
        link(source, destination)

    monkeypatch.setattr(os, "link", competing_create)
    with pytest.raises(WorkflowAlreadyExistsError):
        store.create_workflow("example", VALID)
    assert (tmp_path / "example.yaml").read_text() == "name: other\nsteps: []\n"
    assert len(list(tmp_path.iterdir())) == 1


@pytest.fixture
def save_api(tmp_path, monkeypatch):
    monkeypatch.setenv("CRUCIBLE_WORKSPACE_DIR", str(tmp_path / "workspace"))
    service = WorkflowService()
    app = create_app()
    app.dependency_overrides[get_workflow_service] = lambda: service
    with TestClient(app) as client:
        yield client, service


@pytest.mark.parametrize("content", INVALID_CONTENTS)
def test_api_rejects_bad_saves_with_422_and_keeps_original(save_api, content):
    client, service = save_api
    service.create_workflow("example", VALID)
    response = client.put("/api/v1/workflows/example", json={"content": content})
    assert response.status_code == 422, response.text
    assert response.json()["error"] == "invalid_workflow_content"
    assert "Invalid workflow" in response.json()["message"]
    assert service.store.read_workflow("example") == VALID
    response = client.post("/api/v1/workflows", json={"name": "new", "content": content})
    assert response.status_code == 422, response.text
    assert not service.store.workflow_exists("new")


def test_frontend_yaml_round_trips_through_real_pyyaml_and_save_api(save_api):
    gui = Path(__file__).resolve().parents[1] / "crucible_gui"
    node = shutil.which("node")
    if node is None or not (gui / "node_modules/yaml").exists():
        pytest.skip("Cross-runtime regression requires Node and installed GUI dependencies")
    version = subprocess.run(
        [node, "-p", "process.versions.node.split('.')[0]"],
        text=True, capture_output=True, check=True, timeout=5,
    )
    if int(version.stdout.strip()) < 22:
        pytest.skip("Importing the frontend TypeScript helper requires Node 22+")
    # Exercise the actual frontend helper, rather than a separately recreated
    # YAML string or a round trip through only the JavaScript parser.
    script = """
import { serializeWorkflow } from './src/lib/workflow_yaml.ts';
let input = '';
for await (const chunk of process.stdin) input += chunk;
process.stdout.write(serializeWorkflow(JSON.parse(input)));
"""
    literals = ["yes", "no", "on", "off", "2026-11-13", "12:30:00", "null", "", None, True, False, 42]
    workflow = {"name": "example", "steps": [{"step_id": "filter", "key": "filter_rows", "parameters": {
        "condition": {"left": {"column": "Quantity"}, "operator": "=", "right": {"value": 1}},
        "literals": literals,
    }}]}
    content = subprocess.run(
        [node, "--experimental-strip-types", "--input-type=module", "-e", script],
        cwd=gui, input=json.dumps(workflow), text=True, capture_output=True, check=True, timeout=15,
    ).stdout
    assert yaml.safe_load(content) == workflow
    client, _ = save_api
    response = client.post("/api/v1/workflows", json={"name": "example", "content": content})
    assert response.status_code == 201, response.text
    response = client.put("/api/v1/workflows/example", json={"content": content})
    assert response.status_code == 200, response.text
    assert response.json()["content"]["steps"][0]["parameters"]["literals"] == literals
