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
    """Disk-backed cache of the most recent output preview per workflow.

    Each entry is stored as a JSON file named after a SHA-256 hash of the
    workflow's raw (whitespace-trimmed) YAML text, so any edit to the
    workflow naturally invalidates its previous preview without needing
    explicit cache invalidation logic.
    """

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
        preview: list[dict[str, Any]],
        *,
        row_count: int = 0,
        preview_limit: int = 0,
    ) -> str:
        """Cache a run's preview rows against the workflow's current text.

        The column schema is (re-)inferred from `preview` itself via a
        throwaway `polars.DataFrame`, since the caller only has the
        already-materialized row dicts, not the original Polars schema.

        Args:
            raw_workflow_text (str): Raw YAML text of the workflow, used to derive the cache key.
            preview (list[dict[str, Any]]): Preview rows to cache.
            row_count (int, optional): Total row count of the run's output. Defaults to 0.
            preview_limit (int, optional): Row cap that was applied when collecting the preview. Defaults to 0.

        Returns:
            str: Hash of the workflow text used as the cache key/filename.
        """
        workflow_hash = self._hash_workflow_text(raw_workflow_text)
        cache_path = self._get_cache_path(raw_workflow_text)

        cached_preview = CachedPreview(
            data=preview,
            frame_schema={
                column: str(dtype)
                for column, dtype in pl.DataFrame(preview).schema.items()
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
        """Fetch the cached preview matching a workflow's current text.

        Args:
            raw_workflow_text (str): Raw YAML text of the workflow to look up.

        Returns:
            CachedPreview | None: The cached preview, or `None` if there is
                no cache entry, or the cached file is unreadable/invalid (in
                which case it is deleted).
        """
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
        """Fetch the cached preview as a Polars DataFrame.

        Args:
            raw_workflow_text (str): Raw YAML text of the workflow to look up.

        Returns:
            pl.DataFrame | None: The cached preview rows as a DataFrame, or
                `None` if no cache entry exists.
        """
        cached_preview = self.get_preview(raw_workflow_text)

        if cached_preview is None:
            return None

        return pl.DataFrame(cached_preview.data)

    def has_preview(self, raw_workflow_text: str) -> bool:
        """Check whether a cache entry exists for this workflow text.

        Args:
            raw_workflow_text (str): Raw YAML text of the workflow to check.

        Returns:
            bool: `True` if a cached preview file exists.
        """
        return self._get_cache_path(raw_workflow_text).exists()

    def delete_preview(self, raw_workflow_text: str) -> bool:
        """Delete the cache entry for this workflow text, if any.

        Args:
            raw_workflow_text (str): Raw YAML text of the workflow to clear.

        Returns:
            bool: `True` if a cache file was deleted, `False` if none existed.
        """
        cache_path = self._get_cache_path(raw_workflow_text)

        if not cache_path.exists():
            return False

        cache_path.unlink()
        return True

    def clear(self) -> int:
        """Delete every cached preview.

        Returns:
            int: Number of cache files deleted.
        """
        count = 0

        for path in self._cache_dir.glob("*.json"):
            path.unlink()
            count += 1

        return count
