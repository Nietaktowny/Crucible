import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class RegexExtractConfig(BaseModel):
    """
    Configuration for [`RegexExtractStep`][crucible.steps.regex_extract_step.RegexExtractStep].

    `output_column` may match `column` to overwrite it in place, or a new
    name to add the extracted value as an additional column.
    """

    column: ColumnName = Field(
        description="Column to extract text using regex from",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    pattern: str = Field(
        description="Regex pattern to use for text extracting",
        json_schema_extra=build_schema(
            editor='text'
        )
    )
    output_column: ColumnName = Field(
        description="Column to put extracted values into",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column',
            source='input-schema',
            editor='text'
        )
    )
    group_index: int = Field(
        default=1,
        description="Group index to use",
        json_schema_extra=build_schema(\
            editor='number'
        )
    )


class RegexExtractStep(Step):
    """
    Step that extracts a regex capture group from a string column.

    Uses Polars' `str.extract` with the configured `pattern` and
    `group_index`, writing the extracted value into `output_column` (rows
    with no match become null).
    """

    key = "regex_extract"
    name = "Regex Extract"
    description = "Extract text from a column using a regular expression."
    config_model = RegexExtractConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before extracting text.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring the configured column exists, and a
            [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] ensuring
            the configured column is a string column.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["String"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Extract the configured regex group into the configured output column.

        Args:
            data:
                Frame context whose `df` receives the extracted values.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with the extracted column
            added or overwritten.
        """
        result = data.df.with_columns(
            pl.col(self.config.column)
            .str.extract(
                pattern=self.config.pattern,
                group_index=self.config.group_index,
            )
            .alias(self.config.output_column)
        )
        return FrameContext(df=result)