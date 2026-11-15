class FireScopeError(Exception):
    """Base application error."""
class DatasetSchemaError(FireScopeError):
    """Missing or invalid FIRMS columns."""
class NotImplementedStageError(FireScopeError):
    """Requested feature belongs to a later MVP stage."""
