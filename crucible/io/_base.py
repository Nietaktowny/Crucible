from abc import ABC, abstractmethod
from typing import Protocol

import polars as pl

class IOManager(ABC):
    """Base class for IO managers.
    
    IO managers should be classes implementing two basic methods:
    
    - read - that returns `polars.LazyFrame` from source
    - write - that takes `polars.LazyFrame` as input and outputs it
    - kind - variable that should be the unique key describing IO manager
    
    This would let minimize the logic put into steps and decouple 
    IO from step definition.
    
    These functions are also described by ['IOManagerProtocol'][crucible.io._base.IOManagerProtocol].
    """
    
    kind: str
    
    @abstractmethod
    def read(self) -> pl.LazyFrame:
        raise NotImplementedError

    @abstractmethod
    def write(self, frame: pl.LazyFrame) -> int:
        raise NotImplementedError
    
    
class IOManagerProtocol(Protocol):
    """Protocol defining IO manager public functions:

    - read - that returns `polars.LazyFrame` from source
    - write - that takes `polars.LazyFrame` as input and outputs it    
    """
    def read(self) -> pl.LazyFrame: ...
    
    def write(self, frame: pl.LazyFrame) -> int: ...