

class EngineError(Exception):
    """Base class for all Crucible engine related errors.
    All custom exceptions should derive from this class.
    """

class ColumnNotFoundError(EngineError):
    """Exception raised when column is missing in DataFrame"""
    
class ColumnTypeMismatchError(EngineError):
    """Exception raised when trying to perform actions on column with data type not supporting this action"""
    

class InvalidWorkflowPlan(EngineError):
    """Error raised when workflow plan is invalid."""