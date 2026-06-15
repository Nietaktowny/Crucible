from typing import Any
from datetime import datetime, UTC
from pydantic import BaseModel, Field


class CachedPreview(BaseModel):
    data: list[dict[str, Any]] 
    frame_schema: dict[str, Any]
    row_count: int = 0
    preview_limit: int = 0
    stored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))