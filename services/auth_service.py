from passlib.context import CryptContext
from utils.jwt_handler import create_jwt_token

# Base de données temporaire
fake_users_db = {}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, password: str):
    if username in fake_users_db:
        return False
    hashed = pwd_context.hash(password)
    fake_users_db[username] = {"username": username, "password": hashed}
    return True


def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["password"]):
        return None
    return create_jwt_token(username)
