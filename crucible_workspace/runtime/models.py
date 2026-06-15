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
    pass


class WorkflowStatus(StrEnum):
    CREATED = 'created'
    SUCCESS = "success"
    FAILED = 'failed'
    WAITING = 'waiting'
    RUNNING = 'running'
    CANCELLED = 'cancelled'

class _WorkflowRunResult(RuntimeModelBase):
    __tablename__ = 'runs'
    
    run_id: Mapped[str] = mapped_column(primary_key=True)
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