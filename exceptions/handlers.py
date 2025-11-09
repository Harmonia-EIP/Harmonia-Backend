from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

from .custom_exceptions import InvalidEmailException


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convertit les erreurs Pydantic (dont email invalide)
    en messages simples au format :
    { "detail": "xxx" }
    """

    error = exc.errors()[0]
    field = error["loc"][-1]
    msg = error["msg"]

    if field == "email" and "email address" in msg:
        raise InvalidEmailException("Email invalide.")


    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


async def invalid_email_exception_handler(request: Request, exc: InvalidEmailException):
    """
    Handler dédié pour votre custom exception InvalidEmailException
    Format volontairement identique aux autres erreurs :
    { "detail": "Email invalide." }
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
