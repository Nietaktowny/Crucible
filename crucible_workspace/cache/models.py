from typing import Any
from datetime import datetime, UTC
from pydantic import BaseModel, Field


class CachedPreview(BaseModel):
    """A workflow run's cached output preview.

    Stored on disk by `PreviewCache`, keyed by a hash of the workflow's raw
    YAML text, so it is automatically invalidated whenever the workflow is
    edited.
    """

    data: list[dict[str, Any]]
    """Preview rows, capped at `preview_limit`."""

    frame_schema: dict[str, Any]
    """Column name to Polars dtype name (as a string), inferred from `data`."""

    row_count: int = 0
    """Total row count of the run's output (may exceed `len(data)`)."""

    preview_limit: int = 0
    """Row cap that was applied when this preview was collected."""

    stored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    """Timestamp at which this preview was cached."""
