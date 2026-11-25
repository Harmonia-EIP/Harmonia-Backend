from enum import Enum

from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    # Auth
    MISSING_PARAM = "MISSING_PARAM"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_EMAIL = "INVALID_EMAIL"
    # Token
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    UNAUTHORIZED = "UNAUTHORIZED"
    # Profile
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    # Roles
    NO_ROLE_SEEDS = "NO_ROLE_SEEDS"
    NO_PERMISSION = "NO_PERMISSION"
    # AI
    AI_URL_NOT_CONFIGURED = "AI_URL_NOT_CONFIGURED"
    AI_NETWORK_ERROR = "AI_NETWORK_ERROR"
    AI_BAD_STATUS = "AI_BAD_STATUS"
    AI_INVALID_JSON = "AI_INVALID_JSON"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # History
    HISTORY_NOT_FOUND = "HISTORY_NOT_FOUND"
    # Avatar
    INVALID_IMAGE = "INVALID_IMAGE"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    UNSUPPORTED_IMAGE_FORMAT = "UNSUPPORTED_IMAGE_FORMAT"
    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"


class AppException(HTTPException):
    """Base de toutes les erreurs métier : status HTTP + error_code + detail."""

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        detail: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# ---------------- AUTH ----------------


class MissingParamException(AppException):
    def __init__(self, param: str):
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.MISSING_PARAM,
            f"Parameter '{param}' is missing.",
        )


class UserAlreadyExistsException(AppException):
    def __init__(self, message: str = "This user already exists."):
        super().__init__(
            status.HTTP_409_CONFLICT, ErrorCode.USER_ALREADY_EXISTS, message
        )


class UserNotFoundException(AppException):
    def __init__(self, message: str = "User not found."):
        super().__init__(status.HTTP_404_NOT_FOUND, ErrorCode.USER_NOT_FOUND, message)


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Invalid credentials."):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.INVALID_CREDENTIALS, message
        )


class InvalidEmailException(AppException):
    def __init__(self, message: str = "Invalid email."):
        super().__init__(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_EMAIL, message)


# ---------------- TOKEN ----------------


class TokenMissingException(AppException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.TOKEN_MISSING, "Missing token."
        )


class TokenInvalidException(AppException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.TOKEN_INVALID, "Invalid token."
        )


class TokenExpiredException(AppException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.TOKEN_EXPIRED, "Expired token."
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized action."):
        super().__init__(status.HTTP_403_FORBIDDEN, ErrorCode.UNAUTHORIZED, message)


# ---------------- PROFILE ----------------


class ProfileNotFoundException(AppException):
    def __init__(self, message: str = "Profile not found."):
        super().__init__(
            status.HTTP_404_NOT_FOUND, ErrorCode.PROFILE_NOT_FOUND, message
        )


# ---------------- ROLES ----------------


class NoRoleSeedsInDatabaseException(AppException):
    def __init__(self, message: str = "No initial roles found in database."):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.NO_ROLE_SEEDS, message
        )


class NoPermissionException(AppException):
    def __init__(self, message: str = "Permission denied for this action."):
        super().__init__(status.HTTP_403_FORBIDDEN, ErrorCode.NO_PERMISSION, message)


# ---------------- AI ----------------


class NoUrlForAIConfiguredException(AppException):
    def __init__(self, message: str = "No URL configured for AI service."):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.AI_URL_NOT_CONFIGURED,
            message,
        )


class AiNetworkException(AppException):
    def __init__(self, message: str = "Network error while calling AI service."):
        super().__init__(
            status.HTTP_502_BAD_GATEWAY, ErrorCode.AI_NETWORK_ERROR, message
        )


class AiBadStatusException(AppException):
    def __init__(self, status_code: int):
        super().__init__(
            status.HTTP_502_BAD_GATEWAY,
            ErrorCode.AI_BAD_STATUS,
            f"AI service returned an invalid HTTP status ({status_code}).",
        )


class AiInvalidJsonException(AppException):
    def __init__(self, message: str = "Invalid AI response (invalid JSON)."):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.AI_INVALID_JSON, message
        )


class AiInvalidResponseException(AppException):
    def __init__(self, message: str = "Invalid AI response structure."):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.AI_INVALID_RESPONSE,
            message,
        )


class HistoryNotFoundException(AppException):
    def __init__(self, message: str = "History not found."):
        super().__init__(
            status.HTTP_404_NOT_FOUND, ErrorCode.HISTORY_NOT_FOUND, message
        )


# ---------------- AVATAR ----------------


class InvalidImageException(AppException):
    def __init__(self, message: str = "Invalid or corrupted image."):
        super().__init__(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_IMAGE, message)


class ImageTooLargeException(AppException):
    def __init__(self, message: str = "Image too large (max 2 MB)."):
        super().__init__(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, ErrorCode.IMAGE_TOO_LARGE, message
        )


class UnsupportedImageFormatException(AppException):
    def __init__(
        self, message: str = "Unsupported image format (use PNG, JPEG, GIF or WebP)."
    ):
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            ErrorCode.UNSUPPORTED_IMAGE_FORMAT,
            message,
        )


# ---------------- RATE LIMIT ----------------


class RateLimitedException(AppException):
    def __init__(self, retry_after: int):
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.RATE_LIMITED,
            "Too many requests, please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
