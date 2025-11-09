from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models.user import User
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

        required_fields = {
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "username": payload.username,
            "email": payload.email,
            "password": payload.password
        }

        for field, value in required_fields.items():
            if value is None or value == "" or str(value).strip() == "":
                raise MissingParamException({field})
        
        if self.db.query(User).filter(User.email == payload.email).first():
            raise UserAlreadyExistsException("Cet email est déjà utilisé.")

        if self.db.query(User).filter(User.username == payload.username).first():
            raise UserAlreadyExistsException("Ce nom d'utilisateur est déjà pris.")

        hashed_pw = pwd_context.hash(payload.password)

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            email=payload.email,
            password=hashed_pw
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Utilisateur créé avec succès",
            "user_id": user.id,
            "token": token
        }

    def signin(self, payload: SignInSchema):
        identifier = payload.identifier
        password = payload.password

        user = (
            self.db.query(User)
            .filter(
                (User.email == identifier) |
                (User.username == identifier)
            )
            .first()
        )

        if not user:
            raise UserNotFoundException("Identifiants incorrects.")

        if not pwd_context.verify(password, user.password):
            raise InvalidCredentialsException("Identifiants incorrects.")

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Connexion réussie",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "token": token
        }

