from sqlalchemy.orm import Session

from utils.jwt_handler import decode_jwt_token
from models.user import User
from models.user_info import UserInfo
from models.user_role import UserRole
from models.role import Role

from schemas.profile import ProfileSchema, ProfileDetailsSchema

from exceptions.custom_exceptions import (
    TokenMissingException,
    TokenInvalidException,
    UserNotFoundException,
    NoPermissionException
)


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
        role = (
            self.db.query(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user.id)
            .first()
        )

        if not role or role.code != "ADMIN":
            raise NoPermissionException("Admin role required")

        return True
    
    def _build_profile_schema(self, user: User) -> ProfileDetailsSchema:

        info = self.db.query(UserInfo).filter(
            UserInfo.user_id == user.id
        ).first()

        if not info:
            raise UserNotFoundException()

        role_code = (
            self.db.query(Role.code)
            .join(UserRole, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user.id)
            .scalar()
        )

        return ProfileDetailsSchema(
            id=user.id,
            first_name=info.first_name,
            last_name=info.last_name,
            username=info.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            role=role_code
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

        role = self.db.query(Role).filter(Role.code == new_role).first()
        if not role:
            raise ValueError("Invalid role code")

        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id
        ).first()

        if user_role:
            user_role.role_id = role.id
        else:
            self.db.add(UserRole(user_id=user_id, role_id=role.id))

        self.db.commit()

    def update_user_active_status(self, user_id: int, is_active: bool):

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)

        return self._build_profile_schema(user)

    def ensure_active_user_from_token(self, token: str) -> User:
        """
        Vérifie :
        - token présent
        - token valide
        - user existe en DB
        - user est actif
        """

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
