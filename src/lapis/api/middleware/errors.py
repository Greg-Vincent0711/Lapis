# api/middleware/errors.py
from src.lapis.api.models.http_models import APIResponse

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class UnauthorizedError(APIError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, 404)

class InvalidLocationError(APIError):
    def __init__(self, message: str = "Invalid location"):
        super().__init__(message, 404)

class ConflictError(APIError):
    def __init__(self, message: str):
        super().__init__(message, 409)

class ValidationError(APIError):
    def __init__(self, message: str):
        super().__init__(message, 400)

class LocationLimitExceededError(APIError):
    def __init__(self, message: str):
        super().__init__(message, 400)

class DataAccessError(APIError):
    def __init__(self, message: str):
        super().__init__(message, 500)


def error_handler_middleware(handler):
    """Catches exceptions and converts to HTTP responses"""
    def wrapper(event, context):
        try:
            return handler(event, context)
        except APIError as e:
            return APIResponse(e.status_code, {"error": e.message}).to_lambda_response()
        except Exception as e:
            # type only: the message can contain user data
            print(f"Unexpected error: {type(e).__name__}")
            return APIResponse(500, {"error": "Internal server error"}).to_lambda_response()
    return wrapper