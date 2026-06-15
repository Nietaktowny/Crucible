from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl
from pydantic import ValidationError

from crucible_workspace.cache.models import CachedPreview
from crucible_workspace.paths import get_runtime_data_dir


class PreviewCache:
    def __init__(self) -> None:
        self._cache_dir = get_runtime_data_dir() / "preview_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash_workflow_text(self, raw_workflow_text: str) -> str:
        normalized_text = raw_workflow_text.strip().encode("utf-8")
        return hashlib.sha256(normalized_text).hexdigest()

    def _get_cache_path(self, raw_workflow_text: str) -> Path:
        workflow_hash = self._hash_workflow_text(raw_workflow_text)
        return self._cache_dir / f"{workflow_hash}.json"

    def save_preview(
        self,
        raw_workflow_text: str,
        preview: pl.DataFrame,
        *,
        row_count: int = 0,
        preview_limit: int = 0,
    ) -> str:
        workflow_hash = self._hash_workflow_text(raw_workflow_text)
        cache_path = self._get_cache_path(raw_workflow_text)

        cached_preview = CachedPreview(
            data=preview.to_dicts(),
            frame_schema={
                column: str(dtype)
                for column, dtype in preview.schema.items()
            },
            row_count=row_count,
            preview_limit=preview_limit,
        )

        payload = {
            "workflow_hash": workflow_hash,
            "preview": cached_preview.model_dump(mode="json"),
        }

        cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return workflow_hash

    def get_preview(self, raw_workflow_text: str) -> CachedPreview | None:
        cache_path = self._get_cache_path(raw_workflow_text)

        if not cache_path.exists():
            return None

        try:
            payload: dict[str, Any] = json.loads(
                cache_path.read_text(encoding="utf-8")
            )

            return CachedPreview.model_validate(payload["preview"])

        except (json.JSONDecodeError, KeyError, TypeError, ValidationError):
            cache_path.unlink(missing_ok=True)
            return None

    def get_preview_frame(self, raw_workflow_text: str) -> pl.DataFrame | None:
        cached_preview = self.get_preview(raw_workflow_text)

        if cached_preview is None:
            return None

        return pl.DataFrame(cached_preview.data)

    def has_preview(self, raw_workflow_text: str) -> bool:
        return self._get_cache_path(raw_workflow_text).exists()

    def delete_preview(self, raw_workflow_text: str) -> bool:
        cache_path = self._get_cache_path(raw_workflow_text)

        if not cache_path.exists():
            return False

        cache_path.unlink()
        return True

    def clear(self) -> int:
        count = 0

        for path in self._cache_dir.glob("*.json"):
            path.unlink()
            count += 1

        return count