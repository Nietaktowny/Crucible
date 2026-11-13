"""Read-only draft previews and full-data filter value searches."""

from typing import NoReturn

import polars as pl

from crucible.models import FrameContext

from crucible.workflow.evaluation import EvaluationError, WorkflowEvaluator
from crucible_server.schemas import (
    FilterValuesRequest, FilterValuesResponse,
    WorkflowPreviewRequest, WorkflowPreviewResponse,
)
from crucible_server.services.workflows import WorkflowService


class WorkflowPreviewService:
    """Read draft frames without touching workflow storage or run history."""

    def __init__(self, workflows: WorkflowService):
        self.evaluator = WorkflowEvaluator(workflows.store.get_workflow_model)

    def _evaluate(self, request: WorkflowPreviewRequest) -> tuple[FrameContext, dict[str, str]]:
        ids = [step.step_id for step in request.workflow.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Workflow step IDs must be unique")
        return self.evaluator.evaluate(
            request.workflow, request.step_id, before=request.before,
        )

    def preview(self, request: WorkflowPreviewRequest) -> WorkflowPreviewResponse:
        """Collect a bounded sample after applying the selected prefix."""
        frame, input_schema = self._evaluate(request)
        try:
            rows = frame.df.limit(request.preview_limit + 1).collect()
        except Exception as exc:
            self._collection_error(request, exc)
        truncated = rows.height > request.preview_limit
        return WorkflowPreviewResponse(
            data=rows.head(request.preview_limit).to_dicts(),
            columns=rows.columns,
            frame_schema=frame.schema,
            input_schema=input_schema,
            step_id=request.step_id,
            truncated=truncated,
            row_count=None if truncated else rows.height,
        )

    def filter_values(self, request: FilterValuesRequest) -> FilterValuesResponse:
        """Search distinct values from the full selected frame."""
        frame, _ = self._evaluate(request)
        schema = frame.df.collect_schema()
        if request.column not in schema:
            raise ValueError(f"Column not found: {request.column}")
        column = pl.col(request.column)
        values = frame.df.select(column).unique()
        if request.search:
            values = values.filter(
                column.cast(pl.String, strict=False).str.contains(request.search, literal=True)
            )
        try:
            collected = values.sort(request.column, nulls_last=False).limit(request.limit + 1).collect()
        except Exception as exc:
            self._collection_error(request, exc)
        return FilterValuesResponse(
            values=collected.head(request.limit).get_column(request.column).to_list(),
            value_type=str(schema[request.column]),
            truncated=collected.height > request.limit,
        )

    def _collection_error(self, request: WorkflowPreviewRequest, error: Exception) -> NoReturn:
        # Lazy data errors can surface after a later step. Re-evaluate only on
        # failure to locate the original transformation (including dependencies).
        self.evaluator.evaluate(
            request.workflow, request.step_id, before=request.before, validate_data=True,
        )
        step = next(step for step in request.workflow.steps if step.step_id == request.step_id)
        raise EvaluationError(str(error), step, request.workflow.name) from error
