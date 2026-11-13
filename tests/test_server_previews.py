import polars as pl
import pytest
from fastapi.testclient import TestClient

from crucible.models import Workflow, StepConfig
from crucible_server.app import create_app
from crucible_server.dependencies import get_workflow_service
from crucible_server.services.workflows import WorkflowService


@pytest.fixture
def preview_api(tmp_path, monkeypatch):
    monkeypatch.setenv("CRUCIBLE_WORKSPACE_DIR", str(tmp_path / "workspace"))
    service = WorkflowService()
    app = create_app()
    app.dependency_overrides[get_workflow_service] = lambda: service
    source = tmp_path / "input.csv"
    pl.DataFrame({"id": range(300)}).write_csv(source)
    workflow = Workflow(name="draft", steps=[StepConfig(key="read_csv", parameters={"path": str(source), "infer_types": True})])
    with TestClient(app) as client:
        yield client, service, workflow


def test_draft_preview_does_not_save_or_record_runs(preview_api):
    client, service, workflow = preview_api
    response = client.post("/api/v1/workflows/draft/preview", json={"workflow": workflow.model_dump(mode="json"), "step_id": workflow.steps[0].step_id})
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["data"]) == 200
    assert body["frame_schema"] == {"id": "Int64"}
    assert body["truncated"] and body["row_count"] is None
    assert service.list_workflows() == []
    assert service.db.get_all_results() == []


def test_api_filter_values_searches_beyond_preview(preview_api):
    client, _, workflow = preview_api
    response = client.post("/api/v1/workflows/draft/filter-values", json={"workflow": workflow.model_dump(mode="json"), "step_id": workflow.steps[0].step_id, "column": "id", "search": "299"})
    assert response.status_code == 200, response.text
    assert response.json() == {"values": [299], "value_type": "Int64", "truncated": False}


def test_api_returns_configured_validation_id_and_rejects_oversized_requests(preview_api):
    client, _, workflow = preview_api
    workflow.steps.append(StepConfig(key="sort_rows"))
    payload = {"workflow": workflow.model_dump(mode="json"), "step_id": workflow.steps[-1].step_id}
    response = client.post("/api/v1/workflows/draft/preview", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["step_id"] == workflow.steps[-1].step_id
    response = client.post("/api/v1/workflows/draft/preview", json={**payload, "preview_limit": 1001})
    assert response.status_code == 422
