from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .custom_exceptions import AppException, ErrorCode


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code.value, "detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    error = exc.errors()[0]
    field = error["loc"][-1]
    msg = error["msg"]

    # Email invalide -> même format que les autres erreurs
    if field == "email" and "email address" in msg:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": ErrorCode.INVALID_EMAIL.value,
                "detail": "Invalid email.",
            },
        )

    return JSONResponse(
        status_code=422,
        content={
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "detail": f"Invalid value for '{field}': {msg}",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)