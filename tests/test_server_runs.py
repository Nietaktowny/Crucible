from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crucible_server.app import create_app
from crucible_server.dependencies import get_run_service, get_workflow_service
from crucible_server.errors import WorkflowNotFoundError, WorkflowRunError
from crucible_server.schemas import WorkflowRunResponse


class FakeWorkflowService:
    def get_workflow_path(self, name: str) -> Path:
        if name == "missing":
            raise WorkflowNotFoundError(name)

        return Path(f"/fake/workflows/{name}.yaml")


class FakeRunService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def run_workflow(
        self,
        workflow_name: str,
        workflow_service: FakeWorkflowService,
        print_plan: bool = False,
    ) -> WorkflowRunResponse:
        self.calls.append((workflow_name, print_plan))

        if workflow_name == "broken":
            raise WorkflowRunError(
                workflow_name=workflow_name,
                reason="boom",
            )

        workflow_service.get_workflow_path(workflow_name)

        return WorkflowRunResponse(
            workflow_name=workflow_name,
            success=True,
            message="Workflow finished successfully.",
        )


@pytest.fixture
def client() -> TestClient:
    app = create_app()

    fake_workflow_service = FakeWorkflowService()
    fake_run_service = FakeRunService()

    app.dependency_overrides[get_workflow_service] = lambda: fake_workflow_service
    app.dependency_overrides[get_run_service] = lambda: fake_run_service

    return TestClient(app)


def test_run_workflow(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs/workflows/example",
        json={
            "print_plan": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "workflow_name": "example",
        "success": True,
        "message": "Workflow finished successfully.",
    }


def test_run_workflow_with_print_plan(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs/workflows/example",
        json={
            "print_plan": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_run_workflow_uses_default_request_body(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs/workflows/example",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["workflow_name"] == "example"


def test_run_workflow_returns_404_when_workflow_missing(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs/workflows/missing",
        json={},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "workflow_not_found"
    assert response.json()["workflow_name"] == "missing"


def test_run_workflow_returns_500_when_core_fails(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs/workflows/broken",
        json={},
    )

    assert response.status_code == 500
    assert response.json()["error"] == "workflow_run_failed"
    assert response.json()["workflow_name"] == "broken"
    assert response.json()["reason"] == "boom"