from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    NoPermissionException,
    TokenInvalidException,
    TokenMissingException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from models.role import ROLE_ADMIN_ID, ROLE_CODE_BY_ID, ROLE_ID_BY_CODE
from models.user import User
from models.user_info import UserInfo
from models.user_params import DEFAULT_LAST_COLOR_ID, UserParams
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
from utils.jwt_handler import create_jwt_token, decode_jwt_token
from utils.password import hash_password, verify_password


def issue_token(user: User) -> str:
    """Token d'accès lié à la version de token courante de l'utilisateur."""
    return create_jwt_token({"sub": user.id, "ver": user.token_version or 0})


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------
    def get_current_user(self, token: str | None) -> User:
        """Utilisateur authentifié par le header Authorization.

        Refuse les tokens absents, invalides, expirés ou révoqués, et les
        comptes désactivés : un compte désactivé ne peut plus rien faire.
        """
        if not token:
            raise TokenMissingException()

        if token.startswith("Bearer "):
            token = token[len("Bearer ") :].strip()

        payload = decode_jwt_token(token)
        if payload is None:
            raise TokenInvalidException()

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException()

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()

        if payload.get("ver", 0) != (user.token_version or 0):
            raise TokenInvalidException()

        if not user.is_active:
            raise NoPermissionException("Account disabled.")

        return user

    # ------------------------------------------------------------------
    def get_or_create_params(self, user_id: int) -> UserParams:
        """Retourne les params de l'utilisateur, en les créant avec la
        palette par défaut s'ils n'existent pas encore."""

        params = self.db.query(UserParams).filter(UserParams.user_id == user_id).first()
        if params:
            return params

        params = UserParams(user_id=user_id, last_color_id=DEFAULT_LAST_COLOR_ID)
        for color_id, color in enumerate(UserParams.DEFAULT_PALETTE, start=1):
            params.set_color(color_id, color)

        self.db.add(params)
        self.db.commit()
        self.db.refresh(params)
        return params

    def get_profile(self, user: User) -> ProfileSchema:
        info = self._get_info(user.id)
        params = self.get_or_create_params(user.id)

        history = [
            HistoryEntrySchema(
                id=h.id,
                name=h.name,
                type=h.type,
                parameters=h.parameters,
                model_id=h.model_id,
                model_name=h.model_name,
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

        info = self._get_info(user.id)
        changes = data.model_dump(exclude_unset=True)

        new_username = changes.get("username")
        if new_username is not None and new_username != info.username:
            if self.username_taken(new_username, exclude_user_id=user.id):
                raise UserAlreadyExistsException("This username is already taken.")

        for field, value in changes.items():
            setattr(info, field, value)

        self._commit_unique("This username is already taken.")
        self.db.refresh(info)

        return self.get_profile(user)

    def update_email(self, user: User, data: UpdateEmailSchema) -> ProfileSchema:
        """Changement d'email : exige le mot de passe actuel."""

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect.")

        if data.new_email != user.email:
            if self.email_taken(data.new_email, exclude_user_id=user.id):
                raise UserAlreadyExistsException("This email is already in use.")

            user.email = data.new_email
            self._commit_unique("This email is already in use.")
            self.db.refresh(user)

        return self.get_profile(user)

    def update_password(self, user: User, data: UpdatePasswordSchema) -> str:
        """Changement de mot de passe : exige l'ancien. Révoque tous les
        tokens existants et renvoie un nouveau token."""

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect.")

        user.password_hash = hash_password(data.new_password)
        user.token_version = (user.token_version or 0) + 1
        self.db.commit()

        return issue_token(user)

    # ------------------------------------------------------------------
    # Unicité (insensible à la casse)
    # ------------------------------------------------------------------
    def email_taken(self, email: str, exclude_user_id: int | None = None) -> bool:
        conditions = [func.lower(User.email) == email.lower()]
        if exclude_user_id is not None:
            conditions.append(User.id != exclude_user_id)
        return self.db.query(User).filter(*conditions).first() is not None

    def username_taken(self, username: str, exclude_user_id: int | None = None) -> bool:
        conditions = [func.lower(UserInfo.username) == username.lower()]
        if exclude_user_id is not None:
            conditions.append(UserInfo.user_id != exclude_user_id)
        return self.db.query(UserInfo).filter(*conditions).first() is not None

    def _commit_unique(self, message: str) -> None:
        """Commit ; une violation d'unicité (requêtes simultanées) devient
        une 409 au lieu d'une 500."""
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise UserAlreadyExistsException(message) from exc

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

        self._get_user(user_id)
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
    # Administration
    # ------------------------------------------------------------------
    def ensure_admin(self, user: User) -> None:
        if user.role_id != ROLE_ADMIN_ID:
            raise NoPermissionException("Admin role required")

    def get_profile_by_id(self, user_id: int) -> ProfileDetailsSchema:
        return self._build_profile_details(self._get_user(user_id))

    def update_user_role(
        self, current_user: User, user_id: int, role_code: str
    ) -> ProfileDetailsSchema:
        # Un admin ne peut pas se retirer ses droits : il reste toujours
        # au moins l'admin qui fait l'action.
        if current_user.id == user_id:
            raise NoPermissionException("You cannot change your own role.")

        user = self._get_user(user_id)
        user.role_id = ROLE_ID_BY_CODE[role_code]
        self.db.commit()
        self.db.refresh(user)

        return self._build_profile_details(user)

    def update_user_active_status(
        self, current_user: User, user_id: int, is_active: bool
    ) -> ProfileDetailsSchema:
        if current_user.id == user_id:
            raise NoPermissionException("You cannot change your own active status.")

        user = self._get_user(user_id)
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)

        return self._build_profile_details(user)

    # ------------------------------------------------------------------
    def _get_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        return user

    def _get_info(self, user_id: int) -> UserInfo:
        info = self.db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
        if not info:
            raise UserNotFoundException()
        return info

    def _build_profile_details(self, user: User) -> ProfileDetailsSchema:
        info = self._get_info(user.id)
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
            role=ROLE_CODE_BY_ID.get(user.role_id),
            palette=params.palette,
            last_color_id=params.last_color_id,
        )
