from sqlalchemy.orm import Session

from utils.jwt_handler import decode_jwt_token
from models.user import User

from exceptions.custom_exceptions import (
    TokenMissingException,
    TokenInvalidException,
    UserNotFoundException
)


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_user(self, token: str):

        if not token:
            raise TokenMissingException()

        print(token)
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()
        print(token)

        payload = decode_jwt_token(token)

        if payload is None:
            raise TokenInvalidException()

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException()

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise UserNotFoundException()

        return user

    def get_profile(self, user: User):
        return user
