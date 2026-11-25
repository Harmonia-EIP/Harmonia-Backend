import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from exceptions.custom_exceptions import TokenExpiredException

load_dotenv()

# HS256 : la clé doit faire au moins 256 bits (32 octets).
MIN_SECRET_LENGTH = 32
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def get_jwt_secret() -> str:
    """Renvoie JWT_SECRET. Refuse de fonctionner sans clé ou avec une clé
    trop courte : une valeur par défaut permettrait de forger des tokens.

    Générer une clé : python -c "import secrets; print(secrets.token_urlsafe(48))"
    """
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be set and at least {MIN_SECRET_LENGTH} characters long."
        )
    return secret


def create_jwt_token(payload: dict) -> str:
    """Crée un JWT signé avec une date d'expiration.

    `payload` doit contenir {"sub": user_id} et peut contenir {"ver": n},
    la version de token de l'utilisateur (incrémentée pour révoquer).
    """
    to_encode = {**payload, "sub": str(payload["sub"])}
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> dict | None:
    """Renvoie le payload, None si le token est invalide.
    Lève TokenExpiredException si le token est expiré."""
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredException() from exc
    except jwt.PyJWTError:
        return None
