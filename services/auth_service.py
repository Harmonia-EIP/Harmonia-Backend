from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    MissingParamException,
    UserAlreadyExistsException,
)
from models.role import ROLE_USER_ID
from models.user import User
from models.user_info import UserInfo
from models.user_params import (
    DEFAULT_LAST_COLOR_ID,
    DEFAULT_PALETTE,
    UserParams,
)
from schemas.auth import SignInSchema, SignUpSchema
from services.profile_service import ProfileService, issue_token
from utils.password import burn_password_check, hash_password, verify_password

INVALID_CREDENTIALS = "Invalid credentials."


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
                raise MissingParamException(field)

        profiles = ProfileService(self.db)

        if profiles.email_taken(payload.email):
            raise UserAlreadyExistsException("This email is already in use.")

        if profiles.username_taken(payload.username):
            raise UserAlreadyExistsException("This username is already taken.")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            is_active=True,
            role_id=ROLE_USER_ID,
            token_version=0,
        )
        self.db.add(user)

        try:
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
                color_1=DEFAULT_PALETTE[0],
                color_2=DEFAULT_PALETTE[1],
                color_3=DEFAULT_PALETTE[2],
                last_color_id=DEFAULT_LAST_COLOR_ID,
            )
            self.db.add(user_params)
            self.db.commit()
        except IntegrityError as exc:
            # Deux inscriptions simultanées avec le même email / pseudo
            self.db.rollback()
            raise UserAlreadyExistsException(
                "This email or username is already in use."
            ) from exc

        self.db.refresh(user)
        self.db.refresh(user_params)

        return {
            "message": "User created successfully",
            "user_id": user.id,
            "username": user_info.username,
            "email": user.email,
            "token": issue_token(user),
            "palette": user_params.palette,
            "last_color_id": user_params.last_color_id,
            "avatar_url": None,
        }

    def signin(self, payload: SignInSchema):
        identifier = payload.identifier.strip().lower()
        password = payload.password

        if "@" in identifier:
            user = (
                self.db.query(User).filter(func.lower(User.email) == identifier).first()
            )
        else:
            user = (
                self.db.query(User)
                .join(UserInfo)
                .filter(func.lower(UserInfo.username) == identifier)
                .first()
            )

        # Même réponse (et même temps de calcul) que le compte existe ou non :
        # on ne révèle pas quels emails / pseudos sont inscrits.
        if not user:
            burn_password_check(password)
            raise InvalidCredentialsException(INVALID_CREDENTIALS)

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException(INVALID_CREDENTIALS)

        if not user.is_active:
            raise InvalidCredentialsException("Account disabled.")

        user_info = user.info
        params = ProfileService(self.db).get_or_create_params(user.id)

        return {
            "message": "Login successful",
            "user_id": user.id,
            "username": user_info.username if user_info else None,
            "email": user.email,
            "token": issue_token(user),
            "palette": params.palette,
            "last_color_id": params.last_color_id,
            "avatar_url": user_info.avatar_url if user_info else None,
        }
