from typing import Optional


class AdapterError(Exception):
    """Base exception for adapter errors."""
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AdapterError):
    """Resource not found."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404
        )

class ValidationError(AdapterError):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=400)

class LLMError(AdapterError):
    """LLM call failed."""
    def __init__(self, message: str):
        super().__init__(code="LLM_ERROR", message=message, status_code=502)


class FeatureNotImplementedError(AdapterError):
    """Feature exists in API contract but is not implemented yet."""
    def __init__(self, feature: str, message: Optional[str] = None):
        super().__init__(
            code="NOT_IMPLEMENTED",
            message=message or f"{feature} is not implemented yet",
            status_code=501
        )