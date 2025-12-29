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
    MissingParamException
)
from utils.jwt_handler import create_jwt_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def signup(self, payload: SignUpSchema):

        # Vérif basique des champs requis
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

        # Email déjà utilisé ?
        if self.db.query(User).filter(User.email == payload.email).first():
            raise UserAlreadyExistsException("Cet email est déjà utilisé.")

        # Username déjà utilisé ? (dans UserInfo maintenant)
        if self.db.query(UserInfo).filter(UserInfo.username == payload.username).first():
            raise UserAlreadyExistsException("Ce nom d'utilisateur est déjà pris.")

        # Hash du mot de passe
        hashed_pw = pwd_context.hash(payload.password)

        # Création de l'utilisateur (table users)
        user = User(
            email=payload.email,
            password_hash=hashed_pw,
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()  # pour récupérer user.id sans commit

        # Création des infos utilisateur (table user_info)
        user_info = UserInfo(
            user_id=user.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
        )
        self.db.add(user_info)

        # Attribution du rôle USER par défaut
        role_user = self.db.query(Role).filter(Role.code == "USER").first()
        if role_user is None:
            # là, si ça arrive, c’est vraiment un problème de config serveur
            # tu peux lever une exception interne ou HTTP 500
            raise Exception("Rôle USER manquant en base. Vérifier le script de seed.")

        user_role = UserRole(user_id=user.id, role_id=role_user.id)
        self.db.add(user_role)

        # Validation en base
        self.db.commit()
        self.db.refresh(user)

        # Création du token JWT
        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Utilisateur créé avec succès",
            "user_id": user.id,
            "token": token,
        }

    def signin(self, payload: SignInSchema):
        identifier = payload.identifier
        password = payload.password

        # Identifier peut être un email ou un username
        if "@" in identifier:
            # Login via email
            user = (
                self.db.query(User)
                .filter(User.email == identifier)
                .first()
            )
        else:
            # Login via username -> jointure avec user_info
            user = (
                self.db.query(User)
                .join(UserInfo)
                .filter(UserInfo.username == identifier)
                .first()
            )

        if not user:
            raise UserNotFoundException("Identifiants incorrects.")

        # Vérif du hash
        if not pwd_context.verify(password, user.password_hash):
            raise InvalidCredentialsException("Identifiants incorrects.")

        if not user.is_active:
            raise InvalidCredentialsException("Compte désactivé.")

        token = create_jwt_token({"sub": user.id})

        # On va chercher les infos de profil pour répondre
        info = user.info  # relation 1–1

        return {
            "message": "Connexion réussie",
            "user_id": user.id,
            "username": info.username if info else None,
            "email": user.email,
            "token": token,
        }
