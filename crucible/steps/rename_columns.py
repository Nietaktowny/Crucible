import polars as pl
from pydantic import BaseModel

from crucible.models import Step

class RenameColumnsConfig(BaseModel):
    mapping: dict[str, str]
class RenameColumnsStep(Step):
    key = "rename_columns"
    name = "Rename Columns"
    description = "Rename columns based on a provided mapping."
    config_model = RenameColumnsConfig

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.rename(self.config.mapping)