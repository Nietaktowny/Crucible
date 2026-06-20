import logging
from typing import Any
import inspect

import crucible.steps as steps
from crucible.models import (
    StepConfig,
    StepProtocol,
    Step
)


logger = logging.getLogger(__name__)

class StepsRegistry:
    """Registry class that should be used to manage step definitions.
    It should provide things like:
    
    - step discovery
    - deserializing step definition from StepConfig into actual class supporting StepProtocol
    - generating json schema for step
    """
    def __init__(self) -> None:
        self._steps_cls = self._discover_steps()
        logger.debug("Discovered steps: %s", list(self._steps_cls.keys()))
    
    def _discover_steps(self) -> dict[str, type[StepProtocol]]:
        """Discovers all steps defined in ['steps'][crucible.steps] module
        by searching the step names defined in `__all__`.

        Returns:
            dict[str, type[StepProtocol]]: Dictionary where step key is key, and step class is value for all steps found.
        """
        return {
            step_cls.key: step_cls
            for step_name in steps.__all__
            if inspect.isclass(step_cls := getattr(steps, step_name))
            and issubclass(step_cls, Step)
            and step_cls is not Step
        }
    
    def get_step(self, key: str, step_config: StepConfig) -> StepProtocol:
        """Get step instance initialized with passed step configuration.

        Args:
            key (str): Step class key.
            step_config (StepConfig): Step configuration to use.

        Raises:
            ValueError: If passed key is not found in registry.

        Returns:
            StepProtocol: Initialized step instance.
        """
        step_cls = self._steps_cls.get(key)
        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")
        
        return step_cls(config=step_config)
    
    def list_step_keys(self) -> list[str]:
        """Get all discovered step definitions.

        Returns:
            list[str]: List of step keys.
        """
        return [self.get_step_definition(key) for key in self._steps_cls.keys()]
    
    def get_step_definition(self, key: str) -> dict[str, Any]:
        """Get step definition with basic information and configuration model as json schema.

        Args:
            key (str): Step key that should identify step class.

        Raises:
            ValueError: If step key is not found in registry.

        Returns:
            dict[str, Any]: Dictionary containing basic step definition values.
        """
        step_cls = self._steps_cls.get(key)

        if not step_cls:
            raise ValueError(f"Step with key '{key}' not found in registry.")

        return {
            "key": step_cls.key,
            "name": step_cls.name,
            "description": step_cls.description,
            "schema": step_cls.config_model.model_json_schema(),
        }
        
    