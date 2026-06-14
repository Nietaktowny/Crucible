from typing import Any, Literal, ClassVar
from pathlib import Path
from enum import StrEnum
from abc import ABC, abstractmethod
from uuid import uuid4
from typing import Protocol, Mapping
from datetime import datetime

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

class FrameContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    df: pl.LazyFrame
    preview: pl.DataFrame | None = None
    row_count: int | None = None

    @computed_field
    @property
    def schema(self) -> dict[str, str] | None:
        if isinstance(self.df, pl.LazyFrame):
            return {
                name: str(dtype)
                for name, dtype in self.df.collect_schema().items()
            }
        return None
        
    def collect(self) -> pl.DataFrame:
        return self.df.collect()

class StepGuardProtocol(Protocol):
    def check(self, data: FrameContext) -> None: ...

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

    def guards(self) -> list[StepGuardProtocol]:
        return []

    @abstractmethod
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
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
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        pass
    
class StepProtocol(Protocol):
    def execute(self, data: FrameContext) -> FrameContext: ...
    
    def guards(self) -> list[StepGuardProtocol]: ...

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
    
class WorkflowRunConfig(BaseModel):
    inspect: bool = False
    preview_limit: int = 500

class WorkflowStatus(StrEnum):
    CREATED = 'created'
    SUCCESS = "success"
    FAILED = 'failed'
    WAITING = 'waiting'
    RUNNING = 'running'
    CANCELLED = 'cancelled'

class WorkflowRuntimeStatistics(BaseModel):
    total_steps: int = 0
    system_steps: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_time: float = 0.0

class WorkflowErrorContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    error: Exception
    step_id: str
    step_name: str
    frame_schema: dict[str, str] | None = None

class WorkflowRunResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    status: WorkflowStatus = WorkflowStatus.CREATED
    preview: pl.DataFrame | None = None
    row_count: int | None = None
    error: WorkflowErrorContext | None = None
    statistics: WorkflowRuntimeStatistics = Field(default_factory=WorkflowRuntimeStatistics)
    
    @computed_field
    @property
    def success(self) -> bool:
        return self.status == WorkflowStatus.SUCCESS