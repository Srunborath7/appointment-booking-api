import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .enum import StatusCode

try:
    from .lib.translate import get_translation
except ImportError:
    def get_translation(key: str) -> str:
        translations = {
            "field_cannot_empty": "Field cannot be empty",
            "invalid_parameters": "Invalid parameters",
            "internal_server_error": "Internal server error",
        }
        return translations.get(key, key)

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base for all application domain errors."""
    status_code: int = StatusCode.BAD_REQUEST
    code: int = StatusCode.BAD_REQUEST

    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)


class BadRequestError(AppException):
    """Malformed request."""
    status_code = StatusCode.BAD_REQUEST
    code = StatusCode.BAD_REQUEST


class AuthenticationError(AppException):
    """Authentication issue."""
    status_code = StatusCode.UNAUTHORIZED
    code = StatusCode.UNAUTHORIZED


class AuthorizationError(AppException):
    """Permission issue."""
    status_code = StatusCode.FORBIDDEN
    code = StatusCode.FORBIDDEN


class NotFoundError(AppException):
    """Resource is missing."""
    status_code = StatusCode.NOT_FOUND
    code = StatusCode.NOT_FOUND


class ConflictError(AppException):
    """Duplicate or conflicting data."""
    status_code = StatusCode.CONFLICT
    code = StatusCode.CONFLICT


class ValidationError(AppException):
    """Validation error."""
    status_code = StatusCode.UNPROCESSABLE_ENTITY
    code = StatusCode.UNPROCESSABLE_ENTITY


class TooManyRequestsError(AppException):
    """Rate limiting."""
    status_code = StatusCode.TOO_MANY_REQUESTS
    code = StatusCode.TOO_MANY_REQUESTS


class ServerError(AppException):
    """Unexpected server error."""
    status_code = StatusCode.INTERNAL_SERVER_ERROR
    code = StatusCode.INTERNAL_SERVER_ERROR


def _error_body(code: int, msg: str) -> dict:
    return {"code": code, "msg": msg, "data": None}

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.msg),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Flatten Pydantic's error list into a single human-readable message so
    # validation failures use the same {code, msg, data} envelope as the rest
    # of the API instead of FastAPI's default {"detail": [...]} body.
    errors = exc.errors()
    if errors:
        first = errors[0]
        # loc is like ("body", "school_code"); drop the source segment.
        field = ".".join(str(part) for part in first.get("loc", ())[1:])
        # Missing fields and empty values get one standard message instead
        # of Pydantic's wording, which varies by field type.
        is_empty = first.get("type") == "missing" or (
            "input" in first and first["input"] in ("", None)
        )
        if is_empty:
            detail = get_translation("field_cannot_empty")
        else:
            detail = first.get("msg", get_translation("invalid_parameters"))
        msg = f"{field}: {detail}" if field else detail
    else:
        msg = get_translation("invalid_parameters")
    return JSONResponse(
        status_code=StatusCode.UNPROCESSABLE_ENTITY,
        content=_error_body(StatusCode.UNPROCESSABLE_ENTITY, msg),
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Covers HTTPException raised anywhere plus router-level 404/405s.
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.status_code, str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=StatusCode.INTERNAL_SERVER_ERROR,
        content=_error_body(StatusCode.INTERNAL_SERVER_ERROR, get_translation("internal_server_error")),
    )
