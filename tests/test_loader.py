import json

import pytest
import yaml
from pydantic import ValidationError

from crucible.models import Workflow
from crucible.workflow.loader import WorkflowLoader


def sample_raw_workflow() -> dict:
    return {
        "name": "test_workflow",
        "steps": [
            {
                "key": "select_columns",
                "parameters": {
                    "columns": ["A", "B"],
                },
            },
            {
                "key": "filter_rows",
                "parameters": {
                    "column": "A",
                    "operator": ">",
                    "value": 10,
                },
            },
        ],
    }


def test_load_yaml_file_returns_workflow(tmp_path) -> None:
    path = tmp_path / "workflow.yaml"
    path.write_text(
        yaml.safe_dump(sample_raw_workflow(), sort_keys=False),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    workflow = loader.load(path)

    assert isinstance(workflow, Workflow)
    assert workflow.name == "test_workflow"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].key == "select_columns"
    assert workflow.steps[0].parameters == {"columns": ["A", "B"]}


def test_load_yml_file_returns_workflow(tmp_path) -> None:
    path = tmp_path / "workflow.yml"
    path.write_text(
        yaml.safe_dump(sample_raw_workflow(), sort_keys=False),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    workflow = loader.load(path)

    assert workflow.name == "test_workflow"
    assert workflow.steps[1].key == "filter_rows"


def test_load_json_file_returns_workflow(tmp_path) -> None:
    path = tmp_path / "workflow.json"
    path.write_text(
        json.dumps(sample_raw_workflow(), indent=2),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    workflow = loader.load(path)

    assert isinstance(workflow, Workflow)
    assert workflow.name == "test_workflow"
    assert len(workflow.steps) == 2


def test_load_accepts_string_path(tmp_path) -> None:
    path = tmp_path / "workflow.yaml"
    path.write_text(
        yaml.safe_dump(sample_raw_workflow()),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    workflow = loader.load(str(path))

    assert workflow.name == "test_workflow"


def test_load_missing_file_raises_file_not_found_error(tmp_path) -> None:
    path = tmp_path / "missing.yaml"

    loader = WorkflowLoader()

    with pytest.raises(FileNotFoundError, match="Workflow file does not exist"):
        loader.load(path)


def test_load_unsupported_extension_raises_value_error(tmp_path) -> None:
    path = tmp_path / "workflow.txt"
    path.write_text("name: test", encoding="utf-8")

    loader = WorkflowLoader()

    with pytest.raises(ValueError, match="Unsupported workflow file format"):
        loader.load(path)


def test_load_invalid_workflow_schema_raises_validation_error(tmp_path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        yaml.safe_dump({"steps": []}),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    with pytest.raises(ValidationError):
        loader.load(path)


def test_load_raw_yaml_returns_dict(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.yaml"
    path.write_text(
        yaml.safe_dump(raw, sort_keys=False),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    result = loader.load_raw(path)

    assert result == raw


def test_load_raw_json_returns_dict(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.json"
    path.write_text(
        json.dumps(raw, indent=2),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    result = loader.load_raw(path)

    assert result == raw


def test_load_raw_missing_file_raises_file_not_found_error(tmp_path) -> None:
    loader = WorkflowLoader()

    with pytest.raises(FileNotFoundError, match="Workflow file does not exist"):
        loader.load_raw(tmp_path / "missing.yaml")


def test_load_raw_unsupported_extension_raises_value_error(tmp_path) -> None:
    path = tmp_path / "workflow.unsupported"
    path.write_text("{}", encoding="utf-8")

    loader = WorkflowLoader()

    with pytest.raises(ValueError, match="Unsupported workflow file format"):
        loader.load_raw(path)


def test_save_raw_yaml_writes_yaml_file(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.yaml"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)

    assert path.exists()
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == raw


def test_save_raw_yml_writes_yaml_file(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.yml"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)

    assert path.exists()
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == raw


def test_save_raw_json_writes_json_file(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.json"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)

    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == raw


def test_save_raw_preserves_unicode_in_yaml(tmp_path) -> None:
    raw = {
        "name": "zażółć_gęślą_jaźń",
        "steps": [
            {
                "key": "rename_columns",
                "parameters": {
                    "mapping": {
                        "źródło": "wartość",
                    },
                },
            },
        ],
    }

    path = tmp_path / "workflow.yaml"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)

    text = path.read_text(encoding="utf-8")

    assert "zażółć_gęślą_jaźń" in text
    assert "źródło" in text
    assert yaml.safe_load(text) == raw


def test_save_raw_preserves_unicode_in_json(tmp_path) -> None:
    raw = {
        "name": "zażółć_gęślą_jaźń",
        "steps": [],
    }

    path = tmp_path / "workflow.json"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)

    text = path.read_text(encoding="utf-8")

    assert "zażółć_gęślą_jaźń" in text
    assert json.loads(text) == raw


def test_save_raw_unsupported_extension_raises_value_error(tmp_path) -> None:
    loader = WorkflowLoader()

    with pytest.raises(ValueError, match="Unsupported workflow file format"):
        loader.save_raw(sample_raw_workflow(), tmp_path / "workflow.txt")


def test_save_yaml_writes_workflow_model(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())
    path = tmp_path / "workflow.yaml"

    loader = WorkflowLoader()

    loader.save(workflow, path)

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert loaded["name"] == "test_workflow"
    assert loaded["steps"][0]["key"] == "select_columns"
    assert loaded["steps"][0]["parameters"] == {"columns": ["A", "B"]}


def test_save_yml_writes_workflow_model(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())
    path = tmp_path / "workflow.yml"

    loader = WorkflowLoader()

    loader.save(workflow, path)

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert loaded["name"] == "test_workflow"
    assert len(loaded["steps"]) == 2


def test_save_json_writes_workflow_model(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())
    path = tmp_path / "workflow.json"

    loader = WorkflowLoader()

    loader.save(workflow, path)

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded["name"] == "test_workflow"
    assert loaded["steps"][1]["key"] == "filter_rows"


def test_save_unsupported_extension_raises_value_error(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())

    loader = WorkflowLoader()

    with pytest.raises(ValueError, match="Unsupported workflow file format"):
        loader.save(workflow, tmp_path / "workflow.txt")


def test_roundtrip_raw_yaml(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.yaml"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)
    loaded = loader.load_raw(path)

    assert loaded == raw


def test_roundtrip_raw_json(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.json"

    loader = WorkflowLoader()

    loader.save_raw(raw, path)
    loaded = loader.load_raw(path)

    assert loaded == raw


def test_roundtrip_workflow_yaml(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())
    path = tmp_path / "workflow.yaml"

    loader = WorkflowLoader()

    loader.save(workflow, path)
    loaded = loader.load(path)

    assert loaded.name == workflow.name
    assert [step.key for step in loaded.steps] == [
        step.key for step in workflow.steps
    ]


def test_roundtrip_workflow_json(tmp_path) -> None:
    workflow = Workflow.model_validate(sample_raw_workflow())
    path = tmp_path / "workflow.json"

    loader = WorkflowLoader()

    loader.save(workflow, path)
    loaded = loader.load(path)

    assert loaded.name == workflow.name
    assert loaded.model_dump() == workflow.model_dump()


def test_read_file_yaml_directly(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.yaml"
    path.write_text(
        yaml.safe_dump(raw),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    assert loader._read_file(path) == raw


def test_read_file_json_directly(tmp_path) -> None:
    raw = sample_raw_workflow()
    path = tmp_path / "workflow.json"
    path.write_text(
        json.dumps(raw),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    assert loader._read_file(path) == raw


def test_read_file_unsupported_extension_directly(tmp_path) -> None:
    path = tmp_path / "workflow.toml"
    path.write_text("name = 'test'", encoding="utf-8")

    loader = WorkflowLoader()

    with pytest.raises(ValueError, match="Unsupported workflow file format"):
        loader._read_file(path)


def test_load_logs_workflow_name(tmp_path, caplog) -> None:
    path = tmp_path / "workflow.yaml"
    path.write_text(
        yaml.safe_dump(sample_raw_workflow()),
        encoding="utf-8",
    )

    loader = WorkflowLoader()

    with caplog.at_level("INFO"):
        loader.load(path)

    assert "Loaded workflow: test_workflow" in caplog.text