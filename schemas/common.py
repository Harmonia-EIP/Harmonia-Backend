"""Types et validateurs partagés par les schémas d'entrée."""

from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, EmailStr, StringConstraints

USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_BYTES = 72  # limite de bcrypt
PROMPT_MAX_LENGTH = 500


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def _lower(value: str) -> str:
    return value.lower()


def _check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_BYTES} bytes")
    return value


# Emails : espaces retirés puis minuscules (unicité insensible à la casse).
NormalizedEmail = Annotated[EmailStr, BeforeValidator(_strip), AfterValidator(_lower)]

# Mot de passe : jamais modifié (pas de strip), longueur bornée pour bcrypt.
Password = Annotated[
    str,
    StringConstraints(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_BYTES),
    AfterValidator(_check_password_bytes),
]
