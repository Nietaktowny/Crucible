from __future__ import annotations

import hashlib
import json

from crucible_workspace import PreviewCache, CachedPreview


RAW_WORKFLOW_TEXT = """
steps:
  - key: read_csv
    path: input.csv
"""


def test_cache_directory_is_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )

    PreviewCache()

    assert (tmp_path / "preview_cache").exists()
    assert (tmp_path / "preview_cache").is_dir()


def test_save_preview_stores_cached_preview_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    preview = [
        {"name": "Alice", "amount": 10},
        {"name": "Bob", "amount": 20},
    ]

    workflow_hash = cache.save_preview(
        RAW_WORKFLOW_TEXT,
        preview,
        row_count=100,
        preview_limit=2,
    )

    expected_hash = hashlib.sha256(
        RAW_WORKFLOW_TEXT.strip().encode("utf-8")
    ).hexdigest()

    cache_path = tmp_path / "preview_cache" / f"{expected_hash}.json"
    payload = json.loads(cache_path.read_text(encoding="utf-8"))

    assert workflow_hash == expected_hash
    assert cache_path.exists()

    assert payload["workflow_hash"] == expected_hash
    assert payload["preview"]["data"] == [
        {"name": "Alice", "amount": 10},
        {"name": "Bob", "amount": 20},
    ]
    assert payload["preview"]["frame_schema"] == {
        "name": "String",
        "amount": "Int64",
    }
    assert payload["preview"]["row_count"] == 100
    assert payload["preview"]["preview_limit"] == 2
    assert payload["preview"]["stored_at"] is not None


def test_get_preview_returns_cached_preview_model(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    preview = [{"name": "Alice", "amount": 10}]

    cache.save_preview(
        RAW_WORKFLOW_TEXT,
        preview,
        row_count=50,
        preview_limit=1,
    )

    cached_preview = cache.get_preview(RAW_WORKFLOW_TEXT)

    assert isinstance(cached_preview, CachedPreview)
    assert cached_preview.data == [{"name": "Alice", "amount": 10}]
    assert cached_preview.frame_schema == {
        "name": "String",
        "amount": "Int64",
    }
    assert cached_preview.row_count == 50
    assert cached_preview.preview_limit == 1
    assert cached_preview.stored_at is not None


def test_get_preview_frame_returns_polars_dataframe(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    preview = [
        {"name": "Alice", "amount": 10},
        {"name": "Bob", "amount": 20},
    ]

    cache.save_preview(RAW_WORKFLOW_TEXT, preview)

    frame = cache.get_preview_frame(RAW_WORKFLOW_TEXT)

    assert frame is not None
    assert frame.to_dicts() == [
        {"name": "Alice", "amount": 10},
        {"name": "Bob", "amount": 20},
    ]


def test_get_preview_returns_none_when_cache_file_does_not_exist(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    assert cache.get_preview(RAW_WORKFLOW_TEXT) is None
    assert cache.get_preview_frame(RAW_WORKFLOW_TEXT) is None


def test_has_preview_returns_true_when_preview_exists(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    cache.save_preview(RAW_WORKFLOW_TEXT, [{"x": 1}])

    assert cache.has_preview(RAW_WORKFLOW_TEXT) is True


def test_has_preview_returns_false_when_preview_does_not_exist(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    assert cache.has_preview(RAW_WORKFLOW_TEXT) is False


def test_delete_preview_deletes_existing_preview(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    cache.save_preview(RAW_WORKFLOW_TEXT, [{"x": 1}])

    was_deleted = cache.delete_preview(RAW_WORKFLOW_TEXT)

    assert was_deleted is True
    assert cache.has_preview(RAW_WORKFLOW_TEXT) is False


def test_delete_preview_returns_false_when_preview_does_not_exist(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    assert cache.delete_preview(RAW_WORKFLOW_TEXT) is False


def test_clear_deletes_all_preview_files(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    cache.save_preview("workflow 1", [{"x": 1}])
    cache.save_preview("workflow 2", [{"y": 2}])

    deleted_count = cache.clear()

    assert deleted_count == 2
    assert list((tmp_path / "preview_cache").glob("*.json")) == []


def test_clear_returns_zero_when_cache_is_empty(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    assert cache.clear() == 0


def test_same_workflow_text_with_outer_whitespace_uses_same_hash(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    first_hash = cache.save_preview(
        "  steps:\n  - key: test  ",
        [{"x": 1}],
    )
    second_hash = cache.save_preview(
        "steps:\n  - key: test",
        [{"x": 2}],
    )

    cached_preview = cache.get_preview("steps:\n  - key: test")

    assert first_hash == second_hash
    assert cached_preview is not None
    assert cached_preview.data == [{"x": 2}]


def test_get_preview_deletes_invalid_json_file_and_returns_none(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    cache_path = cache._get_cache_path(RAW_WORKFLOW_TEXT)
    cache_path.write_text("{invalid json", encoding="utf-8")

    result = cache.get_preview(RAW_WORKFLOW_TEXT)

    assert result is None
    assert not cache_path.exists()


def test_get_preview_deletes_invalid_payload_and_returns_none(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "crucible_workspace.cache.preview_cache.get_runtime_data_dir",
        lambda: tmp_path,
    )
    cache = PreviewCache()

    cache_path = cache._get_cache_path(RAW_WORKFLOW_TEXT)
    cache_path.write_text(
        json.dumps(
            {
                "workflow_hash": "abc",
                "preview": {
                    "frame_schema": {"x": "Int64"},
                    "row_count": 1,
                    "preview_limit": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    result = cache.get_preview(RAW_WORKFLOW_TEXT)

    assert result is None
    assert not cache_path.exists()