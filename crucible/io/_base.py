from abc import ABC, abstractmethod
from typing import Protocol

import polars as pl

from crucible.models import IOConfig

class IOManager(ABC):
    kind: str
    
    @abstractmethod
    def read(self, config: IOConfig) -> pl.LazyFrame:
        raise NotImplementedError

    @abstractmethod
    def write(self, frame: pl.LazyFrame, config: IOConfig) -> int:
        raise NotImplementedError
    
    
class IOManagerProtocol(Protocol):
    def read(self, config: IOConfig) -> pl.LazyFrame: ...
    
    def write(self, frame: pl.LazyFrame, config: IOConfig) -> int: ...