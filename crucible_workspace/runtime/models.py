from pathlib import Path
from enum import StrEnum
from datetime import datetime
from typing import Any

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy import (
    String,
    JSON,
    Integer
)

class RuntimeModelBase(DeclarativeBase):
    """Declarative base class shared by all `crucible_workspace` ORM models."""

    pass


class WorkflowStatus(StrEnum):
    """Mirrors `crucible.models.WorkflowStatus` for the ORM layer.

    Kept as a separate enum (rather than importing the engine's) so the
    storage layer has no hard dependency on the execution engine's models.
    """

    CREATED = 'created'
    SUCCESS = "success"
    FAILED = 'failed'
    WAITING = 'waiting'
    RUNNING = 'running'
    CANCELLED = 'cancelled'

class _WorkflowRunResult(RuntimeModelBase):
    """ORM row for one recorded workflow run.

    A flattened, SQL-friendly mirror of `crucible.models.WorkflowRunResult`:
    nested statistics and error-context fields are stored as top-level
    columns instead of a nested structure, since SQLite has no native
    nested-object column type. Note that the preview payload itself is
    intentionally NOT persisted here (`is_preview` only records whether one
    existed) — previews are cached separately via `PreviewCache`.
    """

    __tablename__ = 'runs'

    run_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(default=WorkflowStatus.CREATED, nullable=False)
    is_preview: Mapped[bool] = mapped_column(default=False)
    row_count: Mapped[int | None] = mapped_column(nullable=True)
    is_error: Mapped[bool] = mapped_column(nullable=True)

    #statistics
    total_steps: Mapped[int] = mapped_column(default=0)
    system_steps: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    total_time: Mapped[float] = mapped_column(default=0.0)

    #error context
    error: Mapped[str | None] = mapped_column(nullable=True)
    errored_step_id: Mapped[str | None] = mapped_column(nullable=True)
    errored_step_name: Mapped[str | None] = mapped_column(nullable=True)
    errored_frame_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
