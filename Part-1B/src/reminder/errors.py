"""Service-failure types for the reminder agent."""


class ModelServiceError(Exception):
    """Raised when model configuration or the model service is unavailable."""
