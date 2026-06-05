import logging

import crucible.steps as steps
from crucible.models import (
    IOConfig,
    StepConfig,
    StepProtocol,
    Step
)
from crucible.io import IOManager

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