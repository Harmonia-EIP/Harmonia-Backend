from fastapi import HTTPException, status


# ------------------------------------------------------
#  AUTH / SIGNUP / SIGNIN EXCEPTIONS
# ------------------------------------------------------

class MissingParamException(HTTPException):
    def __init__(self, param: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le paramètre '{param}' est manquant."
        )


class UserAlreadyExistsException(HTTPException):
    def __init__(self, message: str = "Cet utilisateur existe déjà."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class UserNotFoundException(HTTPException):
    def __init__(self, message: str = "Utilisateur introuvable."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class InvalidCredentialsException(HTTPException):
    def __init__(self, message: str = "Identifiants invalides."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

class InvalidEmailException(Exception):
    def __init__(self, message: str = "Email invalide."):
        self.message = message
        super().__init__(message)


# ------------------------------------------------------
#  TOKEN / AUTHENTICATION EXCEPTIONS
# ------------------------------------------------------

class TokenMissingException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant."
        )


class TokenInvalidException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide."
        )


class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré."
        )


class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "Action non autorisée."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )


# ------------------------------------------------------
#  PROFILE / USER DATA EXCEPTIONS
# ------------------------------------------------------

class ProfileNotFoundException(HTTPException):
    def __init__(self, message: str = "Profil introuvable."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
