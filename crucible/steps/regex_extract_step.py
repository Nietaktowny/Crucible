import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class RegexExtractConfig(BaseModel):
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
    key = "regex_extract"
    name = "Regex Extract"
    description = "Extract text from a column using a regular expression."
    config_model = RegexExtractConfig

    def guards(self) -> list[StepGuardProtocol]:
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
        result = data.df.with_columns(
            pl.col(self.config.column)
            .str.extract(
                pattern=self.config.pattern,
                group_index=self.config.group_index,
            )
            .alias(self.config.output_column)
        )
        return FrameContext(df=result)