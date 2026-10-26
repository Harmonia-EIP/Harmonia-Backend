from passlib.context import CryptContext
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    MissingParamException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from models.user import User
from models.user_info import UserInfo
from models.user_params import (
    DEFAULT_LAST_COLOR_ID,
    DEFAULT_PALETTE,
    UserParams,
    build_palette,
)
from schemas.auth import SignInSchema, SignUpSchema
from utils.jwt_handler import create_jwt_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3


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

        if self.db.query(User).filter(User.email == payload.email).first():
            raise UserAlreadyExistsException("This email is already in use.")

        if (
            self.db.query(UserInfo)
            .filter(UserInfo.username == payload.username)
            .first()
        ):
            raise UserAlreadyExistsException("This username is already taken.")

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
            color_1=DEFAULT_PALETTE[0],
            color_2=DEFAULT_PALETTE[1],
            color_3=DEFAULT_PALETTE[2],
            last_color_id=DEFAULT_LAST_COLOR_ID,
        )
        self.db.add(user_params)

        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(user_params)

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "User created successfully",
            "user_id": user.id,
            "username": user_info.username if user_info else None,
            "email": user.email,
            "palette": user_params.palette,
            "last_color_id": user_params.last_color_id,
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
            raise UserNotFoundException("Invalid credentials.")

        if not pwd_context.verify(password, user.password_hash):
            raise InvalidCredentialsException("Invalid credentials.")

        if not user.is_active:
            raise InvalidCredentialsException("Account disabled.")

        user_info = user.info
        user_params = user.params

        token = create_jwt_token({"sub": user.id})

        return {
            "message": "Login successful",
            "user_id": user.id,
            "username": user_info.username if user_info else None,
            "email": user.email,
            "palette": (
                user_params.palette if user_params else build_palette(*DEFAULT_PALETTE)
            ),
            "last_color_id": (
                user_params.last_color_id if user_params else DEFAULT_LAST_COLOR_ID
            ),
            "token": token,
        }
