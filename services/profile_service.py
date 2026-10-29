from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    NoPermissionException,
    TokenInvalidException,
    TokenMissingException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from models.user import User
from models.user_info import UserInfo
from models.user_params import UserParams
from schemas.history import HistoryEntrySchema
from schemas.profile import (
    ProfileDetailsSchema,
    ProfileSchema,
    UpdateEmailSchema,
    UpdatePasswordSchema,
    UpdateProfileSchema,
)
from schemas.user_params import UpdatePaletteSchema, UserParamsResponse
from services.history_service import HistoryService
from utils.jwt_handler import decode_jwt_token
from utils.password import hash_password, verify_password

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

    def get_or_create_params(self, user_id: int) -> UserParams:
        """Retourne les params de l'utilisateur, en les créant avec la
        palette par défaut s'ils n'existent pas encore."""

        params = self.db.query(UserParams).filter(UserParams.user_id == user_id).first()
        if params:
            return params

        params = UserParams(user_id=user_id, last_color_id=1)
        for color_id, color in enumerate(UserParams.DEFAULT_PALETTE, start=1):
            params.set_color(color_id, color)

        self.db.add(params)
        self.db.commit()
        self.db.refresh(params)
        return params

    def get_profile(self, user: User) -> ProfileSchema:

        info = self.db.query(UserInfo).filter(UserInfo.user_id == user.id).first()
        if not info:
            raise UserNotFoundException()

        params = self.get_or_create_params(user.id)

        history = [
            HistoryEntrySchema(
                id=h.id,
                name=h.name,
                type=h.type,
                parameters=h.parameters,
                created_at=h.created_at,
                last_used_at=h.last_used_at,
            )
            for h in HistoryService(self.db).list_for_user(user.id)
        ]

        return ProfileSchema(
            id=user.id,
            first_name=info.first_name,
            last_name=info.last_name,
            username=info.username,
            email=user.email,
            avatar_url=info.avatar_url,
            created_at=user.created_at,
            palette=params.palette,
            last_color_id=params.last_color_id,
            history=history,
        )

    # ------------------------------------------------------------------
    # Mise à jour du compte (soi-même uniquement)
    # ------------------------------------------------------------------
    def update_profile(self, user: User, data: UpdateProfileSchema) -> ProfileSchema:
        """Met à jour pseudo, prénom, nom. Seuls les champs envoyés sont
        modifiés. L'avatar passe par AvatarService (upload)."""

        info = self.db.query(UserInfo).filter(UserInfo.user_id == user.id).first()
        if not info:
            raise UserNotFoundException()

        changes = data.model_dump(exclude_unset=True)

        new_username = changes.get("username")
        if new_username is not None and new_username != info.username:
            taken = (
                self.db.query(UserInfo)
                .filter(UserInfo.username == new_username, UserInfo.user_id != user.id)
                .first()
            )
            if taken:
                raise UserAlreadyExistsException("This username is already taken.")

        for field, value in changes.items():
            setattr(info, field, value)

        self.db.commit()
        self.db.refresh(info)

        return self.get_profile(user)

    def update_email(self, user: User, data: UpdateEmailSchema) -> ProfileSchema:
        """Changement d'email : exige le mot de passe actuel."""

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect.")

        if data.new_email != user.email:
            taken = (
                self.db.query(User)
                .filter(User.email == data.new_email, User.id != user.id)
                .first()
            )
            if taken:
                raise UserAlreadyExistsException("This email is already in use.")

            user.email = data.new_email
            self.db.commit()
            self.db.refresh(user)

        return self.get_profile(user)

    def update_password(self, user: User, data: UpdatePasswordSchema) -> None:
        """Changement de mot de passe : exige l'ancien."""

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect.")

        user.password_hash = hash_password(data.new_password)
        self.db.commit()

    # ------------------------------------------------------------------
    # Palette
    # ------------------------------------------------------------------
    def update_palette(
        self,
        current_user: User,
        user_id: int,
        data: UpdatePaletteSchema,
    ) -> UserParamsResponse:
        """Met à jour une partie ou la totalité de la palette et/ou la
        pastille active. Accès : soi-même ou admin. La validation (ids 1..3,
        hex, au moins un champ) est faite par UpdatePaletteSchema (422)."""

        if current_user.id != user_id and current_user.role_id != ROLE_ADMIN_ID:
            raise NoPermissionException("You can only update your own palette")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        params = self.get_or_create_params(user_id)

        if data.colors:
            for item in data.colors:
                params.set_color(item.id, item.color)

        if data.last_color_id is not None:
            params.last_color_id = data.last_color_id

        self.db.commit()
        self.db.refresh(params)

        return UserParamsResponse(
            user_id=user_id,
            palette=params.palette,
            last_color_id=params.last_color_id,
        )

    # ------------------------------------------------------------------
    # Rôles
    # ------------------------------------------------------------------
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

        params = self.get_or_create_params(user.id)

        return ProfileDetailsSchema(
            id=user.id,
            first_name=info.first_name,
            last_name=info.last_name,
            username=info.username,
            email=user.email,
            avatar_url=info.avatar_url,
            created_at=user.created_at,
            is_active=user.is_active,
            role=self._role_code_from_id(user.role_id),
            palette=params.palette,
            last_color_id=params.last_color_id,
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
