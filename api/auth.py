from fastapi import APIRouter
from pydantic import BaseModel
from services.auth_service import create_user, authenticate_user
from models.response_model import ApiResponse

router = APIRouter()

class SignupData(BaseModel):
    username: str
    password: str

class SigninData(BaseModel):
    username: str
    password: str


@router.post("/signup", response_model=ApiResponse)
def signup(data: SignupData):
    success = create_user(data.username, data.password)

    if not success:
        return ApiResponse(
            status="error",
            code=400,
            message="Username already exists"
        )

    return ApiResponse(
        status="success",
        code=201,
        message="User created successfully",
        data={"username": data.username}
    )


@router.post("/signin", response_model=ApiResponse)
def signin(data: SigninData):
    token = authenticate_user(data.username, data.password)

    if not token:
        return ApiResponse(
            status="error",
            code=401,
            message="Invalid credentials"
        )

    return ApiResponse(
        status="success",
        code=200,
        message="Login successful",
        data={"token": token}
    )
