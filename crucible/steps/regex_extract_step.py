import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext


class RegexExtractConfig(BaseModel):
    column: str
    pattern: str
    output_column: str
    group_index: int = 1


class RegexExtractStep(Step):
    key = "regex_extract"
    name = "Regex Extract"
    description = "Extract text from a column using a regular expression."
    config_model = RegexExtractConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data.with_columns(
            pl.col(self.config.column)
            .str.extract(
                pattern=self.config.pattern,
                group_index=self.config.group_index,
            )
            .alias(self.config.output_column)
        )