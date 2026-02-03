from sqlalchemy.orm import Session

from utils.jwt_handler import decode_jwt_token
from models.user import User
from models.user_info import UserInfo

from schemas.profile import ProfileSchema, ProfileDetailsSchema

from exceptions.custom_exceptions import (
    TokenMissingException,
    TokenInvalidException,
    UserNotFoundException,
    NoPermissionException
)

ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_user(self, token: str):

        if not token:
            raise TokenMissingException()

        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()

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

    def get_profile(self, user: User) -> ProfileSchema:

        info = self.db.query(UserInfo).filter(UserInfo.user_id == user.id).first()
        if not info:
            raise UserNotFoundException()

        return ProfileSchema(
            id=user.id,
            first_name=info.first_name,
            last_name=info.last_name,
            username=info.username,
            email=user.email,
            created_at=user.created_at,
        )

    def ensure_admin(self, user: User):
        if user.role_id != ROLE_ADMIN_ID:
            raise NoPermissionException("Admin role required")
        return True

    def ensure_staff_or_admin(self, user: User):
        if user.role_id not in (ROLE_ADMIN_ID, ROLE_STAFF_ID):
            raise NoPermissionException("Staff or admin role required")
        return True

    def _role_code_from_id(self, role_id: int | None) -> str | None:
        if role_id == ROLE_ADMIN_ID:
            return "ADMIN"
        if role_id == ROLE_STAFF_ID:
            return "STAFF"
        if role_id == ROLE_USER_ID:
            return "USER"
        return None

    def _role_id_from_code(self, role_code: str | None) -> int | None:
        if not role_code:
            return None
        rc = role_code.strip().upper()
        if rc == "ADMIN":
            return ROLE_ADMIN_ID
        if rc == "STAFF":
            return ROLE_STAFF_ID
        if rc == "USER":
            return ROLE_USER_ID
        return None

    def _build_profile_schema(self, user: User) -> ProfileDetailsSchema:

        info = self.db.query(UserInfo).filter(UserInfo.user_id == user.id).first()
        if not info:
            raise UserNotFoundException()

        return ProfileDetailsSchema(
            id=user.id,
            first_name=info.first_name,
            last_name=info.last_name,
            username=info.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            role=self._role_code_from_id(user.role_id),
        )

    def get_profile_by_id(self, user_id: int) -> ProfileDetailsSchema:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        return self._build_profile_schema(user)

    def update_user_role(self, user_id: int, new_role: str):

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        new_role_id = self._role_id_from_code(new_role)
        if new_role_id is None:
            raise ValueError("Invalid role code")

        user.role_id = new_role_id
        self.db.commit()
        self.db.refresh(user)

        return self._build_profile_schema(user)

    def update_user_active_status(self, user_id: int, is_active: bool):

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)

        return self._build_profile_schema(user)

    def ensure_active_user_from_token(self, token: str) -> User:

        if not token:
            raise TokenMissingException()

        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()

        payload = decode_jwt_token(token)
        if payload is None:
            raise TokenInvalidException()

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException()

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        if not user.is_active:
            raise NoPermissionException("Compte inactif ou désactivé")

        return user