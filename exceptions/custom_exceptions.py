from fastapi import HTTPException, status


# ------------------------------------------------------
#  AUTH / SIGNUP / SIGNIN EXCEPTIONS
# ------------------------------------------------------

class MissingParamException(HTTPException):
    def __init__(self, param: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter '{param}' is missing."
        )


class UserAlreadyExistsException(HTTPException):
    def __init__(self, message: str = "This user already exists."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class UserNotFoundException(HTTPException):
    def __init__(self, message: str = "User not found."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class InvalidCredentialsException(HTTPException):
    def __init__(self, message: str = "Invalid credentials."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )


class InvalidEmailException(Exception):
    def __init__(self, message: str = "Invalid email."):
        self.message = message
        super().__init__(message)


# ------------------------------------------------------
#  TOKEN / AUTHENTICATION EXCEPTIONS
# ------------------------------------------------------

class TokenMissingException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token."
        )


class TokenInvalidException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token."
        )


class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token."
        )


class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "Unauthorized action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


# ------------------------------------------------------
#  PROFILE / USER DATA EXCEPTIONS
# ------------------------------------------------------

class ProfileNotFoundException(HTTPException):
    def __init__(self, message: str = "Profile not found."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


# ------------------------------------------------------
#  ROLE / PERMISSION EXCEPTIONS
# ------------------------------------------------------

class NoRoleSeedsInDatabaseException(HTTPException):
    def __init__(self, message: str = "No initial roles found in database."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


class NoPermissionException(HTTPException):
    def __init__(self, message: str = "Permission denied for this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


# ------------------------------------------------------
#  AI
# ------------------------------------------------------

class NoUrlForAIConfiguredException(HTTPException):
    def __init__(self, message: str = "No URL configured for AI service."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


class AiNetworkException(HTTPException):
    def __init__(self, message: str = "Network error while calling AI service."):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message
        )


class AiBadStatusException(HTTPException):
    def __init__(self, status_code: int):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service returned an invalid HTTP status ({status_code})."
        )


class AiInvalidJsonException(HTTPException):
    def __init__(self, message: str = "Invalid AI response (invalid JSON)."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


class AiInvalidResponseException(HTTPException):
    def __init__(self, message: str = "Invalid AI response structure."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )