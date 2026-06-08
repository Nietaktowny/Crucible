import logging
from typing import Any, get_args, get_origin, Union
from types import UnionType
from copy import deepcopy

import crucible.steps as steps
from crucible.models import (
    IOConfig,
    StepConfig,
    StepProtocol,
    Step
)
from crucible.io import IOManager
from pydantic import BaseModel
from pydantic_core import PydanticUndefined


logger = logging.getLogger(__name__)

class StepsRegistry:
    def __init__(self) -> None:
        self._steps_cls = self._discover_steps()
        logger.debug("Discovered steps: %s", list(self._steps_cls.keys()))
    
    def _discover_steps(self) -> dict[str, type[StepProtocol]]:
        return {step_cls.key: step_cls for step_cls in steps.__all__ if issubclass(step_cls, Step)}
    
    def get_step(self, key: str, step_config: StepConfig, io_manager: IOManager | None = None) -> StepProtocol:
        step_cls = self._steps_cls.get(key)
        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")
        
        return step_cls(config=step_config)
    
    def get_model_class(self, key: str) -> type | None:
        step_cls = self._steps_cls.get(key)
        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")
        return getattr(step_cls, "config_model", None)

    def _placeholder_for(self, annotation: Any) -> Any:
        origin = get_origin(annotation)
        args = get_args(annotation)

        if annotation is Any:
            return None

        if annotation is str:
            return ""

        if annotation is int:
            return 0

        if annotation is float:
            return 0.0

        if annotation is bool:
            return False

        if origin is list:
            return []

        if origin is dict:
            return {}

        if origin in {Union, UnionType}:
            non_none_args = [arg for arg in args if arg is not type(None)]

            if not non_none_args:
                return None

            return self._placeholder_for(non_none_args[0])

        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return self._template_from_model(annotation)

        return None


    def _template_from_model(self, model_cls: type[BaseModel]) -> dict[str, Any]:
        template = {}

        for field_name, field in model_cls.model_fields.items():
            if field.default is not PydanticUndefined:
                template[field_name] = deepcopy(field.default)
                continue

            if field.default_factory is not None:
                template[field_name] = field.default_factory()
                continue

            template[field_name] = self._placeholder_for(field.annotation)

        return template
    
    def get_step_template(self, key: str) -> dict[str, Any]:
        step_cls = self._get_step_cls(key)
        config_model = getattr(step_cls, "config_model", None)

        template = {
            "key": key,
            "name": getattr(step_cls, "name", key),
            "description": getattr(step_cls, "description", ""),
            "parameters": {},
        }

        if config_model is None:
            return template

        template["parameters"] = self._template_from_model(config_model)
        return template
    
    def list_step_keys(self) -> list[str]:
        return sorted(self._steps_cls.keys())
    
    def _get_step_cls(self, key: str) -> type[StepProtocol]:
        step_cls = self._steps_cls.get(key)

        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")

        return step_cls