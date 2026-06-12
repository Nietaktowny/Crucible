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
        self.calls: list[tuple[str, bool, int, bool]] = []

    def run_workflow(
        self,
        workflow_name: str,
        workflow_service: FakeWorkflowService,
        print_plan: bool = False,
        preview_limit: int = 200,
        inspect: bool = True,
    ) -> WorkflowRunResponse:
        self.calls.append(
            (
                workflow_name,
                print_plan,
                preview_limit,
                inspect,
            )
        )

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
            preview=[
                {
                    "name": "Alice",
                    "value": 1,
                },
                {
                    "name": "Bob",
                    "value": 2,
                },
            ],
            row_count=2,
        )


@pytest.fixture
def fake_run_service() -> FakeRunService:
    return FakeRunService()


@pytest.fixture
def client(fake_run_service: FakeRunService) -> TestClient:
    app = create_app()

    fake_workflow_service = FakeWorkflowService()

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
        "preview": [
            {
                "name": "Alice",
                "value": 1,
            },
            {
                "name": "Bob",
                "value": 2,
            },
        ],
        "row_count": 2,
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
    assert response.json()["success"] is True
    assert response.json()["preview"] == [
        {
            "name": "Alice",
            "value": 1,
        },
        {
            "name": "Bob",
            "value": 2,
        },
    ]
    assert response.json()["row_count"] == 2


def test_run_workflow_passes_request_options_to_run_service(
    client: TestClient,
    fake_run_service: FakeRunService,
) -> None:
    response = client.post(
        "/api/v1/runs/workflows/example",
        json={
            "print_plan": True,
            "preview_limit": 50,
            "inspect": False,
        },
    )

    assert response.status_code == 200

    assert fake_run_service.calls == [
        (
            "example",
            True,
            50,
            False,
        )
    ]


def test_run_workflow_response_contains_preview_and_row_count(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/runs/workflows/example",
        json={},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["preview"] == [
        {
            "name": "Alice",
            "value": 1,
        },
        {
            "name": "Bob",
            "value": 2,
        },
    ]
    assert body["row_count"] == 2


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