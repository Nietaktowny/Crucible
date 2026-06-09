import pytest
from fastapi.testclient import TestClient

from crucible_server.app import create_app
from crucible_server.dependencies import get_workflow_service
from crucible_server.errors import (
    InvalidWorkflowNameError,
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from crucible_server.schemas import WorkflowResponse, WorkflowSummary


class FakeWorkflowService:
    def __init__(self) -> None:
        self.workflows: dict[str, str] = {
            "example": "name: example\nsteps: []\n",
        }

    def list_workflows(self) -> list[WorkflowSummary]:
        return [
            WorkflowSummary(
                name=name,
                path=f"/fake/workflows/{name}.yaml",
            )
            for name in sorted(self.workflows)
        ]

    def get_workflow(self, name: str) -> WorkflowResponse:
        if name == "bad/name":
            raise InvalidWorkflowNameError(
                "Workflow name may contain only letters, numbers, dots, underscores and dashes"
            )

        if name not in self.workflows:
            raise WorkflowNotFoundError(name)

        return WorkflowResponse(
            name=name,
            path=f"/fake/workflows/{name}.yaml",
            content=self.workflows[name],
        )

    def create_workflow(self, name: str, content: str) -> WorkflowResponse:
        if name == "bad/name":
            raise InvalidWorkflowNameError(
                "Workflow name may contain only letters, numbers, dots, underscores and dashes"
            )

        if name in self.workflows:
            raise WorkflowAlreadyExistsError(name)

        self.workflows[name] = content

        return WorkflowResponse(
            name=name,
            path=f"/fake/workflows/{name}.yaml",
            content=content,
        )

    def update_workflow(self, name: str, content: str) -> WorkflowResponse:
        if name not in self.workflows:
            raise WorkflowNotFoundError(name)

        self.workflows[name] = content

        return WorkflowResponse(
            name=name,
            path=f"/fake/workflows/{name}.yaml",
            content=content,
        )

    def delete_workflow(self, name: str) -> None:
        if name not in self.workflows:
            raise WorkflowNotFoundError(name)

        del self.workflows[name]


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    fake_service = FakeWorkflowService()

    app.dependency_overrides[get_workflow_service] = lambda: fake_service

    return TestClient(app)


def test_list_workflows(client: TestClient) -> None:
    response = client.get("/api/v1/workflows")

    assert response.status_code == 200
    assert response.json() == {
        "workflows": [
            {
                "name": "example",
                "path": "/fake/workflows/example.yaml",
            }
        ]
    }


def test_get_workflow(client: TestClient) -> None:
    response = client.get("/api/v1/workflows/example")

    assert response.status_code == 200
    assert response.json() == {
        "name": "example",
        "path": "/fake/workflows/example.yaml",
        "content": "name: example\nsteps: []\n",
    }


def test_get_workflow_returns_404_when_missing(client: TestClient) -> None:
    response = client.get("/api/v1/workflows/missing")

    assert response.status_code == 404
    assert response.json()["error"] == "workflow_not_found"
    assert response.json()["workflow_name"] == "missing"


def test_create_workflow(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workflows",
        json={
            "name": "new_workflow",
            "content": "name: new_workflow\nsteps: []\n",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "name": "new_workflow",
        "path": "/fake/workflows/new_workflow.yaml",
        "content": "name: new_workflow\nsteps: []\n",
    }


def test_create_workflow_returns_409_when_exists(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workflows",
        json={
            "name": "example",
            "content": "name: example\nsteps: []\n",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"] == "workflow_already_exists"
    assert response.json()["workflow_name"] == "example"


def test_create_workflow_returns_422_when_content_empty(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workflows",
        json={
            "name": "empty",
            "content": "",
        },
    )

    assert response.status_code == 422


def test_update_workflow(client: TestClient) -> None:
    response = client.put(
        "/api/v1/workflows/example",
        json={
            "content": "name: example\nsteps:\n  - key: select_columns\n",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "example",
        "path": "/fake/workflows/example.yaml",
        "content": "name: example\nsteps:\n  - key: select_columns\n",
    }


def test_update_workflow_returns_404_when_missing(client: TestClient) -> None:
    response = client.put(
        "/api/v1/workflows/missing",
        json={
            "content": "name: missing\nsteps: []\n",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"] == "workflow_not_found"
    assert response.json()["workflow_name"] == "missing"


def test_delete_workflow(client: TestClient) -> None:
    response = client.delete("/api/v1/workflows/example")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_workflow_returns_404_when_missing(client: TestClient) -> None:
    response = client.delete("/api/v1/workflows/missing")

    assert response.status_code == 404
    assert response.json()["error"] == "workflow_not_found"
    assert response.json()["workflow_name"] == "missing"