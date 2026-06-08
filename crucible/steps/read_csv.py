from pathlib import Path
<<<<<<< HEAD
from uuid import uuid4
=======
>>>>>>> origin/main

from pydantic import BaseModel

from crucible.io import CsvIOManager
<<<<<<< HEAD
from crucible.models import StepConfig, Step, StepExecutionContext
=======
from crucible.models import StepConfig, Step
>>>>>>> origin/main

import polars as pl

class ReadCsvConfig(BaseModel):
    path: Path
    separator: str = ','
    infer_types: bool = False
<<<<<<< HEAD
    context_store: bool = False
    context_key: str = str(uuid4())
    
=======

>>>>>>> origin/main
class ReadCsvStep(Step):
    key = "read_csv"
    name = "Read CSV File"
    description = "Read data from a CSV file"
    config_model =  ReadCsvConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

<<<<<<< HEAD
    def execute(self, data: pl.LazyFrame = None, context: StepExecutionContext = None) -> pl.LazyFrame:
        df =  self.io_manager.read()
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = df
        return df if data is None else data
=======
    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
>>>>>>> origin/main
