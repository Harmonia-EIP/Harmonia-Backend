import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "default_secret_key")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def create_jwt_token(payload: dict):
    """
    Crée un JWT avec une date d'expiration.
    Payload doit contenir {"sub": user_id}
    """
    to_encode = {**payload, "sub": str(payload["sub"])}

    expire = datetime.datetime.now(datetime.timezone.utc) + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )
    to_encode["exp"] = expire

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except JWTError:
        return None


def get_user_id_from_token(token: str):
    """
    Récupère l'user_id contenu dans le champ 'sub' du token.
    Retourne None si token invalide.
    """
    payload = decode_jwt_token(token)
    if not payload:
        return None

    return payload.get("sub")
