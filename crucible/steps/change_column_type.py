from crucible.models import Step
import polars as pl

POLARS_TYPES = {
    "string": pl.String,
    "text": pl.String,
    "int8": pl.Int8,
    "int16": pl.Int16,
    "int32": pl.Int32,
    "int64": pl.Int64,
    "uint8": pl.UInt8,
    "uint16": pl.UInt16,
    "uint32": pl.UInt32,
    "uint64": pl.UInt64,
    "float32": pl.Float32,
    "float64": pl.Float64,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "datetime": pl.Datetime,
    "time": pl.Time,
}

class ChangeColumnTypeStep(Step):
    key = "change_column_type"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.with_columns([
            pl.col(col).cast(POLARS_TYPES.get(dtype))
            for col, dtype in self.config.column_types.items()
        ])