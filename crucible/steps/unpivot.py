import polars as pl
from pydantic import BaseModel

from crucible.models import Step

class UnpivotConfig(BaseModel):
    on: list[str]
    index: list[str]
    variable_name: str
    value_name: str

class UnpivotStep(Step):
    key = "unpivot"
    name = "Unpivot"
    description = "Unpivot the data from wide to long format."
    config_model = UnpivotConfig

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.unpivot(
            on=self.config.on,
            index=self.config.index,
            variable_name=self.config.variable_name,
            value_name=self.config.value_name,
        )