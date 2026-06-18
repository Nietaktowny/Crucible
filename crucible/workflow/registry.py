import logging
from typing import Any

import crucible.steps as steps
from crucible.models import (
    StepConfig,
    StepProtocol,
    Step
)


logger = logging.getLogger(__name__)

class StepsRegistry:
    def __init__(self) -> None:
        self._steps_cls = self._discover_steps()
        logger.debug("Discovered steps: %s", list(self._steps_cls.keys()))
    
    def _discover_steps(self) -> dict[str, type[StepProtocol]]:
        return {step_cls.key: step_cls for step_cls in steps.__all__ if issubclass(step_cls, Step)}
    
    def get_step(self, key: str, step_config: StepConfig) -> StepProtocol:
        step_cls = self._steps_cls.get(key)
        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")
        
        return step_cls(config=step_config)
    
    def list_step_keys(self) -> list[str]:
        return [self.get_step_definition(key) for key in self._steps_cls.keys()]
    
    def get_step_definition(self, key: str) -> dict[str, Any]:
        step_cls = self._steps_cls.get(key)

        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")

        return {
            "key": step_cls.key,
            "name": step_cls.name,
            "description": step_cls.description,
            "schema": step_cls.config_model.model_json_schema(),
        }
        
    