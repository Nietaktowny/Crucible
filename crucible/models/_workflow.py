from typing import Any, Literal, ClassVar
from pathlib import Path
from enum import StrEnum
from abc import ABC, abstractmethod
from uuid import uuid4
from typing import Protocol, Mapping

from pydantic import BaseModel, ConfigDict, Field, computed_field
import polars as pl

class IOConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    path: Path
    
    @computed_field
    @property
    def type(self) -> Literal['.csv', '.xlsx', '.xls', '.parquet']:
        return self.path.suffix


class StepConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    key: str
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

class StepExecutionContext(BaseModel):
    extra_inputs: dict[str, Any] = Field(default_factory=dict)
    
class Step(ABC):
    key: ClassVar[str]
    name: ClassVar[str]
    description: ClassVar[str]
    config_model: ClassVar[type[BaseModel] | None] = None
    
    def __init__(self, config: StepConfig) -> None:
        super().__init__()
        self.id = str(uuid4())
        self.status = StepStatus.WAITING
        self.config = self.parse_config(config)

    @abstractmethod
    def execute(self, data: pl.LazyFrame, context: StepExecutionContext = None) -> pl.LazyFrame:
        pass
    
    def parse_config(self, config: StepConfig) -> BaseModel | None:
        self.name = config.name or self.name
        self.description = config.description or self.description
        
        if self.config_model is None:
            return None
        return self.config_model(**config.model_dump().get("parameters", {}))

    def __hash__(self) -> int:
        return hash(self.id)
class MultiSourcesStepConfig(StepConfig):
    sources: list[StepConfig]

class MultiSourcesStep(Step):
    @abstractmethod
    def execute(self, data: pl.LazyFrame, context: StepExecutionContext = None) -> pl.LazyFrame:
        pass
    
class StepProtocol(Protocol):
    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame: ...

class Workflow(BaseModel):
    name: str

    steps: list[StepConfig | MultiSourcesStepConfig] = Field(default_factory=list)
    

class StepStatus(StrEnum):
    SUCCESS = "success"
    FAILED = 'failed'
    WAITING = 'waiting'
    RUNNING = 'running'
    

class StepExecutionPlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    step: Step
    config: StepConfig
    status: StepStatus = StepStatus.WAITING

    def __hash__(self) -> int:
        return hash(self.step)

class WorkflowExecutionPlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    workflow: Workflow
    steps_execution_plan: list[StepExecutionPlan]