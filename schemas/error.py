from pydantic import BaseModel

from exceptions.custom_exceptions import ErrorCode


class ErrorResponse(BaseModel):
    error_code: ErrorCode
    detail: str
