from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models.user import User
from models.user_params import UserParams
from models.user_info import UserInfo

from schemas.auth import SignUpSchema, SignInSchema
from exceptions.custom_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException,
    MissingParamException,
)
from utils.jwt_handler import create_jwt_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3

DEFAULT_LAYOUT_ID = 1  # layout par défaut
DEFAULT_THEME_ID  = 1  # thème par défaut (ex: Dark)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def signup(self, payload: SignUpSchema):

        required_fields = {
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "username": payload.username,
            "email": payload.email,
            "password": payload.password,
        }

        for field, value in required_fields.items():
            if value is None or str(value).strip() == "":
                raise MissingParamException({field})

        if self.db.query(User).filter(User.email == payload.email).first():
            raise UserAlreadyExistsException("Cet email est déjà utilisé.")

        if self.db.query(UserInfo).filter(UserInfo.username == payload.username).first():
            raise UserAlreadyExistsException("Ce nom d'utilisateur est déjà pris.")

        hashed_pw = pwd_context.hash(payload.password)

        user = User(
            email=payload.email,
            password_hash=hashed_pw,
            is_active=True,
            role_id=ROLE_USER_ID,
        )
        self.db.add(user)
        self.db.flush()

        user_info = UserInfo(
            user_id=user.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
        )
        self.db.add(user_info)

        user_params = UserParams(
            user_id=user.id,
            layout_id=DEFAULT_LAYOUT_ID,
            theme_id=DEFAULT_THEME_ID
        )
        self.db.add(user_params)

        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(user_params)

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Utilisateur créé avec succès",
            "user_id": user.id,
            "username": user_info.username if user_info else None,
            "email": user.email,
            "layout_id": user_params.layout_id,
            "theme_id": user_params.theme_id,
            "token": token,
        }

    def signin(self, payload: SignInSchema):
        identifier = payload.identifier
        password = payload.password

        if "@" in identifier:
            user = self.db.query(User).filter(User.email == identifier).first()
        else:
            user = (
                self.db.query(User)
                .join(UserInfo)
                .filter(UserInfo.username == identifier)
                .first()
            )

        if not user:
            raise UserNotFoundException("Identifiants incorrects.")

        if not pwd_context.verify(password, user.password_hash):
            raise InvalidCredentialsException("Identifiants incorrects.")

        if not user.is_active:
            raise InvalidCredentialsException("Compte désactivé.")

        user_info = user.info
        user_params = user.params  # <- relation User -> UserParams à créer si ce n'est pas déjà fait

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Connexion réussie",
            "user_id": user.id,
            "username": user_info.username if user_info else None,
            "email": user.email,
            "layout_id": user_params.layout_id if user_params else DEFAULT_LAYOUT_ID,
            "theme_id": user_params.theme_id if user_params else DEFAULT_THEME_ID,
            "token": token,
        }