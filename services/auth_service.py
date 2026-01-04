from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models.user import User
from models.user_info import UserInfo
from models.role import Role
from models.user_role import UserRole

from schemas.auth import SignUpSchema, SignInSchema
from exceptions.custom_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException,
    MissingParamException,
    NoRoleSeedsInDatabaseException
)
from utils.jwt_handler import create_jwt_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

        role_user = self.db.query(Role).filter(Role.code == "USER").first()
        if role_user is None:
            raise NoRoleSeedsInDatabaseException("Rôle USER manquant en base. Vérifier le script de seed.")

        user_role = UserRole(user_id=user.id, role_id=role_user.id)
        self.db.add(user_role)

        self.db.commit()
        self.db.refresh(user)

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Utilisateur créé avec succès",
            "user_id": user.id,
            "token": token,
        }

    def signin(self, payload: SignInSchema):
        identifier = payload.identifier
        password = payload.password

        if "@" in identifier:
            user = (
                self.db.query(User)
                .filter(User.email == identifier)
                .first()
            )
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

        token = create_jwt_token({"sub": user.id})

        info = user.info

        return {
            "message": "Connexion réussie",
            "user_id": user.id,
            "username": info.username if info else None,
            "email": user.email,
            "token": token,
        }
