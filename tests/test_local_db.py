from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from crucible.models import (
    WorkflowErrorContext,
    WorkflowRunResult,
    WorkflowRuntimeStatistics,
    WorkflowStatus,
)
from crucible_workspace.runtime import RuntimeDataStorage


@pytest.fixture
def storage(tmp_path, monkeypatch) -> RuntimeDataStorage:
    monkeypatch.setattr(
        "crucible_workspace.runtime.local_db.get_runtime_data_dir",
        lambda: tmp_path,
    )

    return RuntimeDataStorage()


def make_statistics(
    *,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    total_steps: int = 3,
    system_steps: int = 1,
    total_time: float = 0.25,
) -> WorkflowRuntimeStatistics:
    started = started_at or datetime(2026, 6, 15, 10, 0)
    ended = ended_at or started + timedelta(seconds=1)

    return WorkflowRuntimeStatistics(
        total_steps=total_steps,
        system_steps=system_steps,
        started_at=started,
        ended_at=ended,
        total_time=total_time,
    )


def make_result(
    *,
    run_id: str = "run-1",
    status: WorkflowStatus = WorkflowStatus.SUCCESS,
    row_count: int | None = 10,
    error: WorkflowErrorContext | None = None,
    statistics: WorkflowRuntimeStatistics | None = None,
) -> WorkflowRunResult:
    return WorkflowRunResult(
        run_id=run_id,
        status=status,
        preview=None,
        row_count=row_count,
        error=error,
        statistics=statistics or make_statistics(),
    )


def assert_result_equal(
    actual: WorkflowRunResult,
    expected: WorkflowRunResult,
) -> None:
    assert actual.run_id == expected.run_id
    assert actual.status == expected.status
    assert actual.preview is None
    assert actual.row_count == expected.row_count

    assert actual.statistics.total_steps == expected.statistics.total_steps
    assert actual.statistics.system_steps == expected.statistics.system_steps
    assert actual.statistics.started_at == expected.statistics.started_at
    assert actual.statistics.ended_at == expected.statistics.ended_at
    assert actual.statistics.total_time == expected.statistics.total_time

    if expected.error is None:
        assert actual.error is None
    else:
        assert actual.error is not None
        assert str(actual.error.error) == str(expected.error.error)
        assert actual.error.step_id == expected.error.step_id
        assert actual.error.step_name == expected.error.step_name
        assert actual.error.frame_schema == expected.error.frame_schema


def test_add_result_saves_workflow_run(storage: RuntimeDataStorage) -> None:
    result = make_result(run_id="run-1")

    returned_run_id = storage.add_result(result)
    stored = storage.get_result("run-1")

    assert returned_run_id == "run-1"
    assert stored is not None
    assert_result_equal(stored, result)


def test_get_result_returns_none_for_missing_run(
    storage: RuntimeDataStorage,
) -> None:
    assert storage.get_result("missing-run") is None


def test_get_all_results_returns_newest_started_first(
    storage: RuntimeDataStorage,
) -> None:
    older = make_result(
        run_id="older",
        statistics=make_statistics(
            started_at=datetime(2026, 6, 15, 8, 0),
        ),
    )
    newer = make_result(
        run_id="newer",
        statistics=make_statistics(
            started_at=datetime(2026, 6, 15, 12, 0),
        ),
    )

    storage.add_result(older)
    storage.add_result(newer)

    results = storage.get_all_results()

    assert [result.run_id for result in results] == ["newer", "older"]


def test_update_result_updates_existing_run(
    storage: RuntimeDataStorage,
) -> None:
    original = make_result(
        run_id="run-1",
        status=WorkflowStatus.RUNNING,
        row_count=None,
    )
    updated = make_result(
        run_id="run-1",
        status=WorkflowStatus.SUCCESS,
        row_count=123,
        statistics=make_statistics(
            total_steps=5,
            system_steps=2,
            total_time=1.5,
        ),
    )

    storage.add_result(original)

    was_updated = storage.update_result(updated)
    stored = storage.get_result("run-1")

    assert was_updated is True
    assert stored is not None
    assert_result_equal(stored, updated)


def test_update_result_returns_false_for_missing_run(
    storage: RuntimeDataStorage,
) -> None:
    result = make_result(run_id="missing-run")

    assert storage.update_result(result) is False


def test_upsert_result_inserts_missing_run(
    storage: RuntimeDataStorage,
) -> None:
    result = make_result(run_id="run-1")

    returned_run_id = storage.upsert_result(result)
    stored = storage.get_result("run-1")

    assert returned_run_id == "run-1"
    assert stored is not None
    assert_result_equal(stored, result)


def test_upsert_result_updates_existing_run(
    storage: RuntimeDataStorage,
) -> None:
    original = make_result(
        run_id="run-1",
        status=WorkflowStatus.RUNNING,
        row_count=None,
    )
    updated = make_result(
        run_id="run-1",
        status=WorkflowStatus.CANCELLED,
        row_count=0,
        statistics=make_statistics(total_time=2.75),
    )

    storage.upsert_result(original)

    returned_run_id = storage.upsert_result(updated)
    stored = storage.get_result("run-1")

    assert returned_run_id == "run-1"
    assert stored is not None
    assert_result_equal(stored, updated)


def test_delete_result_deletes_existing_run(
    storage: RuntimeDataStorage,
) -> None:
    result = make_result(run_id="run-1")
    storage.add_result(result)

    was_deleted = storage.delete_result("run-1")

    assert was_deleted is True
    assert storage.get_result("run-1") is None


def test_delete_result_returns_false_for_missing_run(
    storage: RuntimeDataStorage,
) -> None:
    assert storage.delete_result("missing-run") is False


def test_delete_all_results_deletes_all_runs(
    storage: RuntimeDataStorage,
) -> None:
    storage.add_result(make_result(run_id="run-1"))
    storage.add_result(make_result(run_id="run-2"))

    deleted_count = storage.delete_all_results()

    assert deleted_count == 2
    assert storage.get_all_results() == []


def test_delete_all_results_returns_zero_when_empty(
    storage: RuntimeDataStorage,
) -> None:
    assert storage.delete_all_results() == 0


def test_failed_result_preserves_error_context(
    storage: RuntimeDataStorage,
) -> None:
    error = WorkflowErrorContext(
        error=ValueError("Missing column: amount"),
        step_id="step-1",
        step_name="Filter rows",
        frame_schema={"amount": "Int64"},
    )
    result = make_result(
        run_id="failed-run",
        status=WorkflowStatus.FAILED,
        row_count=None,
        error=error,
    )

    storage.add_result(result)
    stored = storage.get_result("failed-run")

    assert stored is not None
    assert stored.status == WorkflowStatus.FAILED
    assert stored.error is not None
    assert str(stored.error.error) == "Missing column: amount"
    assert stored.error.step_id == "step-1"
    assert stored.error.step_name == "Filter rows"
    assert stored.error.frame_schema == {"amount": "Int64"}