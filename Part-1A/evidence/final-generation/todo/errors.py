"""Public exception types for the todo package."""


class TodoError(Exception):
    """Base exception for todo domain failures."""


class ValidationError(TodoError):
    """Raised when public input or state shape is invalid."""


class TaskNotFoundError(TodoError):
    """Raised when a requested task id does not exist."""


class InvalidTransitionError(TodoError):
    """Raised when a status transition is not allowed."""


class StorageError(TodoError):
    """Raised when persisted state cannot be loaded or saved."""
