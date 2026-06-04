import polars as pl

from crucible.models import Step


class SortRowsStep(Step):
    key = "sort_rows"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        by = [column["name"] for column in self.config.columns]

        descending = [
            column["direction"].lower() == "desc"
            for column in self.config.columns
        ]

        return data.sort(
            by=by,
            descending=descending,
        )