from abc import ABC, abstractmethod
from typing import Protocol

import polars as pl

from crucible.models import IOConfig

class IOManager(ABC):
    kind: str
    
    @abstractmethod
    def read(self) -> pl.LazyFrame:
        raise NotImplementedError

    @abstractmethod
    def write(self, frame: pl.LazyFrame) -> int:
        raise NotImplementedError
    
    
class IOManagerProtocol(Protocol):
    def read(self) -> pl.LazyFrame: ...
    
    def write(self, frame: pl.LazyFrame) -> int: ...