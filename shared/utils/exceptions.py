"""
Custom exceptions for the application
"""


class BaseAPIException(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(BaseAPIException):
    """Unauthorized access"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ValidationError(BaseAPIException):
    """Validation error"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)


class ConflictError(BaseAPIException):
    """Resource conflict"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)
