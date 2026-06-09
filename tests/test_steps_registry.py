# tests/test_steps_registry.py

from typing import Any

import pytest
import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepConfig, StepExecutionContext
from crucible.workflow.registry import StepsRegistry


class NoConfigStep(Step):
    key = "no_config"
    name = "No Config Step"
    description = "Step without config model"
    config_model = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


class NestedConfig(BaseModel):
    nested_text: str
    nested_number: int = 7


class FullConfig(BaseModel):
    text: str
    number: int
    ratio: float
    enabled: bool
    anything: Any
    items: list[str]
    mapping: dict[str, int]
    optional_text: str | None
    nested: NestedConfig
    default_text: str = "default"
    default_list: list[str] = Field(default_factory=list)


class FullConfigStep(Step):
    key = "full_config"
    name = "Full Config Step"
    description = "Step with full config model"
    config_model = FullConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


class DefaultsOnlyConfig(BaseModel):
    text: str = "abc"
    number: int = 123
    items: list[str] = Field(default_factory=lambda: ["x"])


class DefaultsOnlyStep(Step):
    key = "defaults_only"
    name = "Defaults Only Step"
    description = "Step with defaults only"
    config_model = DefaultsOnlyConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


@pytest.fixture
def registry() -> StepsRegistry:
    registry = StepsRegistry()
    registry._steps_cls = {
        "no_config": NoConfigStep,
        "full_config": FullConfigStep,
        "defaults_only": DefaultsOnlyStep,
    }
    return registry


def test_discover_steps_returns_mapping_from_step_keys() -> None:
    registry = StepsRegistry()

    discovered = registry._discover_steps()

    assert isinstance(discovered, dict)
    assert all(isinstance(key, str) for key in discovered)
    assert all(issubclass(step_cls, Step) for step_cls in discovered.values())


def test_list_step_keys_returns_sorted_keys(registry: StepsRegistry) -> None:
    assert registry.list_step_keys() == [
        "defaults_only",
        "full_config",
        "no_config",
    ]


def test_get_step_returns_step_instance(registry: StepsRegistry) -> None:
    config = StepConfig(key="no_config")

    step = registry.get_step("no_config", step_config=config)

    assert isinstance(step, NoConfigStep)
    assert step.key == "no_config"


def test_get_step_passes_config_to_step(registry: StepsRegistry) -> None:
    config = StepConfig(
        key="full_config",
        parameters={
            "text": "abc",
            "number": 1,
            "ratio": 1.5,
            "enabled": True,
            "anything": {"x": 1},
            "items": ["a", "b"],
            "mapping": {"a": 1},
            "optional_text": None,
            "nested": {
                "nested_text": "nested",
            },
        },
    )

    step = registry.get_step("full_config", step_config=config)

    assert isinstance(step, FullConfigStep)
    assert step.config.text == "abc"
    assert step.config.number == 1
    assert step.config.nested.nested_text == "nested"
    assert step.config.nested.nested_number == 7


def test_get_step_unknown_key_raises_value_error(registry: StepsRegistry) -> None:
    with pytest.raises(ValueError, match="Step with key 'missing' not found"):
        registry.get_step(
            "missing",
            step_config=StepConfig(key="missing"),
        )


def test_get_model_class_returns_config_model(registry: StepsRegistry) -> None:
    assert registry.get_model_class("full_config") is FullConfig


def test_get_model_class_returns_none_for_step_without_config_model(
    registry: StepsRegistry,
) -> None:
    assert registry.get_model_class("no_config") is None


def test_get_model_class_unknown_key_raises_value_error(
    registry: StepsRegistry,
) -> None:
    with pytest.raises(ValueError, match="Step with key 'missing' not found"):
        registry.get_model_class("missing")


def test_get_step_cls_returns_step_class(registry: StepsRegistry) -> None:
    assert registry._get_step_cls("full_config") is FullConfigStep


def test_get_step_cls_unknown_key_raises_value_error(
    registry: StepsRegistry,
) -> None:
    with pytest.raises(ValueError, match="Step with key 'missing' not found"):
        registry._get_step_cls("missing")


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        (Any, None),
        (str, ""),
        (int, 0),
        (float, 0.0),
        (bool, False),
        (list[str], []),
        (dict[str, int], {}),
        (str | None, ""),
        (int | None, 0),
        (None | float, 0.0),
    ],
)
def test_placeholder_for_basic_types(
    registry: StepsRegistry,
    annotation,
    expected,
) -> None:
    assert registry._placeholder_for(annotation) == expected


def test_placeholder_for_nested_model(registry: StepsRegistry) -> None:
    result = registry._placeholder_for(NestedConfig)

    assert result == {
        "nested_text": "",
        "nested_number": 7,
    }


def test_placeholder_for_unknown_type_returns_none(registry: StepsRegistry) -> None:
    class CustomType:
        pass

    assert registry._placeholder_for(CustomType) is None


def test_template_from_model_uses_placeholders_for_required_fields(
    registry: StepsRegistry,
) -> None:
    template = registry._template_from_model(FullConfig)

    assert template["text"] == ""
    assert template["number"] == 0
    assert template["ratio"] == 0.0
    assert template["enabled"] is False
    assert template["anything"] is None
    assert template["items"] == []
    assert template["mapping"] == {}
    assert template["optional_text"] == ""
    assert template["nested"] == {
        "nested_text": "",
        "nested_number": 7,
    }


def test_template_from_model_uses_defaults_and_default_factories(
    registry: StepsRegistry,
) -> None:
    template = registry._template_from_model(DefaultsOnlyConfig)

    assert template == {
        "text": "abc",
        "number": 123,
        "items": ["x"],
    }


def test_template_from_model_deepcopies_mutable_defaults(
    registry: StepsRegistry,
) -> None:
    class MutableDefaultConfig(BaseModel):
        items: list[str] = ["a"]

    first = registry._template_from_model(MutableDefaultConfig)
    second = registry._template_from_model(MutableDefaultConfig)

    first["items"].append("b")

    assert first["items"] == ["a", "b"]
    assert second["items"] == ["a"]


def test_get_step_template_without_config_model(registry: StepsRegistry) -> None:
    template = registry.get_step_template("no_config")

    assert template == {
        "key": "no_config",
        "name": "No Config Step",
        "description": "Step without config model",
        "parameters": {},
    }


def test_get_step_template_with_config_model(registry: StepsRegistry) -> None:
    template = registry.get_step_template("full_config")

    assert template["key"] == "full_config"
    assert template["name"] == "Full Config Step"
    assert template["description"] == "Step with full config model"

    assert template["parameters"] == {
        "text": "",
        "number": 0,
        "ratio": 0.0,
        "enabled": False,
        "anything": None,
        "items": [],
        "mapping": {},
        "optional_text": "",
        "nested": {
            "nested_text": "",
            "nested_number": 7,
        },
        "default_text": "default",
        "default_list": [],
    }


def test_get_step_template_unknown_key_raises_value_error(
    registry: StepsRegistry,
) -> None:
    with pytest.raises(ValueError, match="Step with key 'missing' not found"):
        registry.get_step_template("missing")


def test_get_step_template_returns_independent_default_factory_values(
    registry: StepsRegistry,
) -> None:
    first = registry.get_step_template("defaults_only")
    second = registry.get_step_template("defaults_only")

    first["parameters"]["items"].append("y")

    assert first["parameters"]["items"] == ["x", "y"]
    assert second["parameters"]["items"] == ["x"]


def test_registry_initializes_with_discovered_steps() -> None:
    registry = StepsRegistry()

    assert isinstance(registry._steps_cls, dict)
    assert registry._steps_cls