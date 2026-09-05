from typing import Any, ClassVar, Protocol
from enum import StrEnum
from abc import ABC, abstractmethod
from uuid import uuid4
from datetime import datetime
import traceback

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer
import polars as pl


class StepConfig(BaseModel):
    """
    Raw workflow step definition loaded from a workflow file.

    This model represents the generic configuration shape used in YAML or JSON
    workflow definitions. Concrete step parameters are stored in `parameters`
    and later validated against the step-specific `config_model`.

    Extra fields are allowed to keep the workflow format extensible.
    """

    model_config = ConfigDict(extra="allow")
    
    step_id: str = Field(default_factory=lambda: str(uuid4()))

    key: str
    """Registry key identifying which step implementation should be used."""

    name: str | None = None
    """Optional human-readable step name."""

    description: str | None = None
    """Optional step description shown in logs, plans, or UI."""

    parameters: dict[str, Any] = Field(default_factory=dict)
    """Raw step-specific parameters."""


class StepExecutionContext(BaseModel):
    """
    Runtime context passed to a step during execution.

    The context stores additional data that is not part of the main input
    frame, for example named source frames used by join or concat steps.
    """

    extra_inputs: dict[str, Any] = Field(default_factory=dict)
    """Additional runtime inputs available to a step."""


class FrameContext(BaseModel):
    """
    Runtime container for the current Polars frame and execution metadata.

    `FrameContext` is passed between workflow steps. It keeps the lazy frame as
    the primary data object and may also carry collected preview data and row
    count information.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pl.LazyFrame
    """Current lazy Polars frame."""

    preview: pl.DataFrame | None = None
    """Optional collected preview of the current frame."""

    row_count: int | None = None
    """Optional row count collected during execution."""

    @computed_field
    @property
    def schema(self) -> dict[str, str] | None:
        """
        Return the current frame schema as stringified column types.

        Returns:
            Mapping from column name to string representation of its Polars
            data type, or `None` when the stored frame is not a LazyFrame.
        """
        if isinstance(self.df, pl.LazyFrame):
            return {
                name: str(dtype)
                for name, dtype in self.df.collect_schema().items()
            }

        return None

    def collect(self) -> pl.DataFrame:
        """
        Collect the current lazy frame.

        Returns:
            Materialized Polars DataFrame.
        """
        return self.df.collect()


class StepGuardProtocol(Protocol):
    """
    Protocol implemented by runtime step guards.

    Guards validate assumptions before or during step execution, such as
    required columns, expected column types, existing files, or valid frame
    types.
    """

    def check(self, data: FrameContext) -> None:
        """
        Validate frame context.

        Args:
            data:
                Current frame context.

        Raises:
            Exception:
                Implementations raise concrete exceptions when validation
                fails.
        """


class Step(ABC):
    """
    Base class for all executable workflow steps.

    A step receives a [`FrameContext`][crucible.models.FrameContext], performs
    one transformation or IO operation, and returns a new `FrameContext`.

    Concrete steps define class-level metadata and optionally a Pydantic
    configuration model used to validate `parameters` from
    [`StepConfig`][crucible.models.StepConfig].
    """

    key: ClassVar[str]
    """Unique step key used by the step registry."""

    name: ClassVar[str]
    """Default human-readable step name."""

    description: ClassVar[str]
    """Default step description."""

    config_model: ClassVar[type[BaseModel] | None] = None
    """Optional Pydantic model used to validate step parameters."""

    def __init__(self, config: StepConfig) -> None:
        """
        Initialize a step instance from raw step configuration.

        Args:
            config:
                Raw step configuration loaded from a workflow definition.
        """
        super().__init__()
        self.id = str(uuid4())
        self.status = StepStatus.WAITING
        self.config = self.parse_config(config)

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return runtime guards required by this step.

        Returns:
            List of guards executed before the step transformation.
        """
        return []

    @abstractmethod
    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Execute the step transformation.

        Args:
            data:
                Current frame context.

            context:
                Optional execution context containing extra runtime inputs.

        Returns:
            Updated frame context.
        """

    def parse_config(self, config: StepConfig) -> BaseModel | None:
        """
        Parse raw step configuration into the step-specific config model.

        The method also applies optional workflow-level overrides for step name
        and description.

        Args:
            config:
                Raw step configuration.

        Returns:
            Parsed step-specific configuration model, or `None` when the step
            has no configuration model.
        """
        self.name = config.name or self.name
        self.description = config.description or self.description

        if self.config_model is None:
            return None

        return self.config_model(**config.model_dump().get("parameters", {}))

    def __hash__(self) -> int:
        """Return a hash based on the generated step identifier."""
        return hash(self.id)


class MultiSourcesStepConfig(StepConfig):
    """
    Step configuration for steps that contain nested source steps.

    This is used by transformations that need more than one input source, such
    as joins or concatenations.
    """

    sources: list[StepConfig]
    """Nested source step configurations."""


class MultiSourcesStep(Step):
    """
    Base class for steps that operate on multiple input sources.

    Multi-source steps still behave like normal steps from the executor
    perspective, but they receive additional input frames through
    [`StepExecutionContext`][crucible.models.StepExecutionContext].
    """

    @abstractmethod
    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Execute a multi-source transformation.

        Args:
            data:
                Primary frame context.

            context:
                Execution context containing additional source frames.

        Returns:
            Updated frame context.
        """


class StepProtocol(Protocol):
    """
    Structural protocol for executable workflow steps.

    This protocol describes the minimum interface required by the registry,
    compiler, and executor without forcing all compatible objects to inherit
    directly from [`Step`][crucible.models.Step].
    """

    key: ClassVar[str]
    name: ClassVar[str]
    description: ClassVar[str]
    config_model: ClassVar[type[BaseModel] | None]

    def execute(self, data: FrameContext) -> FrameContext:
        """Execute the step and return an updated frame context."""

    def guards(self) -> list[StepGuardProtocol]:
        """Return guards required by this step."""


class Workflow(BaseModel):
    """
    Declarative workflow definition.

    A workflow contains an ordered list of step configurations. The compiler
    turns this definition into an executable workflow plan.
    """

    name: str
    """Workflow name."""

    steps: list[StepConfig | MultiSourcesStepConfig] = Field(default_factory=list)
    """Ordered workflow step definitions."""


class StepStatus(StrEnum):
    """Execution status of a single workflow step."""

    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"
    RUNNING = "running"


class StepExecutionPlan(BaseModel):
    """
    Executable plan item for one workflow step.

    The compiler creates this model after resolving a raw step configuration
    into a concrete step instance.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    step: Step
    """Concrete executable step instance."""

    config: StepConfig
    """Original raw step configuration."""

    status: StepStatus = StepStatus.WAITING
    """Current execution status of the planned step."""

    def __hash__(self) -> int:
        """Return a hash based on the underlying step."""
        return hash(self.step)


class WorkflowExecutionPlan(BaseModel):
    """
    Executable workflow plan produced by the compiler.

    The plan contains resolved step instances and metadata about optimizations
    applied before execution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workflow: Workflow
    """Original workflow definition."""

    steps_execution_plan: list[StepExecutionPlan]
    """Ordered executable step plan."""

    applied_optimizations: list[str] = Field(default_factory=list)
    """Names or descriptions of optimizations applied to the workflow."""


class WorkflowRunConfig(BaseModel):
    """
    Runtime options used when executing a workflow.
    """

    inspect: bool = False
    """Whether to collect inspection output during execution."""

    preview_limit: int = 500
    """Maximum number of preview rows to collect."""


class WorkflowStatus(StrEnum):
    """Execution status of a workflow run."""

    CREATED = "created"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"
    RUNNING = "running"
    CANCELLED = "cancelled"


class WorkflowRuntimeStatistics(BaseModel):
    """
    Runtime statistics collected for a workflow execution.
    """

    total_steps: int = 0
    """Total number of planned steps."""

    system_steps: int = 0
    """Number of internal/system steps added by the engine."""

    started_at: datetime | None = None
    """Timestamp when workflow execution started."""

    ended_at: datetime | None = None
    """Timestamp when workflow execution finished."""

    total_time: float = 0.0
    """Total workflow execution time in seconds."""


class WorkflowErrorContext(BaseModel):
    """
    Structured error context captured when workflow execution fails.

    The error context enriches raw exceptions with step and frame information,
    making it easier for the server or UI layer to show useful diagnostics.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    error: Exception
    """Original exception raised during execution."""

    step_id: str
    """Identifier of the step that failed."""

    step_name: str
    """Name of the step that failed."""

    frame_schema: dict[str, str] | None = None
    """Schema visible at the moment of failure, if available."""

    @field_serializer("error", mode='plain')
    def error_to_str(self, value: Exception) -> str:
        return "".join(traceback.format_exception(value))

class WorkflowRunResult(BaseModel):
    """
    Result of a workflow execution.

    This model is returned by the runner and can be serialized by higher-level
    layers such as the server or CLI.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: uuid4().hex)
    """Unique workflow run identifier."""

    name: str
    """Workflow name."""

    status: WorkflowStatus = WorkflowStatus.CREATED
    """Final or current workflow run status."""

    preview: list[dict[str, Any]] | None = None
    """Optional preview dataframe collected from the final result."""

    row_count: int | None = None
    """Optional final row count."""

    error: WorkflowErrorContext | None = None
    """Structured execution error, if the workflow failed."""

    statistics: WorkflowRuntimeStatistics = Field(
        default_factory=WorkflowRuntimeStatistics
    )
    """Runtime statistics collected during execution."""

    @computed_field
    @property
    def success(self) -> bool:
        """
        Return whether the workflow finished successfully.

        Returns:
            `True` when status is `success`, otherwise `False`.
        """
        return self.status == WorkflowStatus.SUCCESS