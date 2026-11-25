from functools import lru_cache

import bcrypt

# bcrypt ne prend en compte que les 72 premiers octets : on tronque
# explicitement (même comportement que passlib, utilisé auparavant).
BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(password), password_hash.encode("ascii"))
    except (ValueError, TypeError, AttributeError):
        return False


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password("timing-equalizer")


def burn_password_check(password: str) -> None:
    """Fait un vrai calcul bcrypt pour rien : un login sur un compte inexistant
    prend alors autant de temps qu'un mauvais mot de passe."""
    verify_password(password, _dummy_hash())
