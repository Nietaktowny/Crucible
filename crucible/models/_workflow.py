from typing import Any, Literal, ClassVar
from pathlib import Path
from enum import StrEnum
from abc import ABC, abstractmethod
from uuid import uuid4
from typing import Protocol

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


class Step(ABC):
    key: ClassVar[str]
    
    def __init__(self, config: StepConfig) -> None:
        super().__init__()
        self.id = str(uuid4())
        self.config = config
    
    @abstractmethod
    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        pass
    
    
class StepProtocol(Protocol):
    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame: ...

class Workflow(BaseModel):
    name: str

    input: IOConfig
    steps: list[StepConfig] = Field(default_factory=list)
    output: IOConfig
    

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


class WorkflowExecutionPlan(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    workflow: Workflow
    steps_execution_plan: list[StepExecutionPlan]