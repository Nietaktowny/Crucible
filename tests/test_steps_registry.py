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

def test_registry_initializes_with_discovered_steps() -> None:
    registry = StepsRegistry()

    assert isinstance(registry._steps_cls, dict)
    assert registry._steps_cls