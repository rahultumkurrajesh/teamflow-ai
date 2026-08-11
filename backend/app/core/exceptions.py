"""Application exception types.

Services raise these domain errors. The API layer translates them into HTTP
responses in one place (see app/main.py), so business code never imports
FastAPI or knows about status codes. That separation is the point.
"""


class AppError(Exception):
    """Base class for all expected, handled errors."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class PermissionError(AppError):
    status_code = 403
    code = "forbidden"
