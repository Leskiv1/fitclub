"""Single error format for the whole API: {"error": {"code", "message", "details"?}}."""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.domain.errors import (
    AppError,
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)

STATUS_BY_ERROR: dict[type[AppError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    BusinessRuleError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """Documented in Swagger for every endpoint that can fail."""

    error: ErrorBody


def error_response(status_code: int, code: str, message: str, details: list[ErrorDetail] | None = None):
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body, exclude_none=True))


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = next(
        (code for error_type, code in STATUS_BY_ERROR.items() if isinstance(exc, error_type)),
        status.HTTP_400_BAD_REQUEST,
    )
    response = error_response(status_code, exc.code, exc.message)
    if isinstance(exc, AuthenticationError):
        response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        ErrorDetail(field=".".join(str(part) for part in err["loc"] if part != "body"), message=err["msg"])
        for err in exc.errors()
    ]
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Некоректні дані запиту", details
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Last line of defence: a constraint violated in the database that the service did not foresee."""
    return error_response(status.HTTP_409_CONFLICT, "conflict", "Операція порушує обмеження цілісності даних")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)


ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Потрібно увійти (немає або недійсний токен)"},
    403: {"model": ErrorResponse, "description": "Недостатньо прав"},
    404: {"model": ErrorResponse, "description": "Не знайдено"},
    409: {"model": ErrorResponse, "description": "Конфлікт з наявними даними"},
    422: {"model": ErrorResponse, "description": "Некоректні дані або порушення бізнес-правила"},
}
