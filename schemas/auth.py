from pydantic import BaseModel, EmailStr, Field

from schemas.user_params import PaletteColorSchema


class SignUpSchema(BaseModel):
    first_name: str = Field(example="Damien")
    last_name: str = Field(example="Chien")
    username: str = Field(example="dogMAN")
    email: EmailStr = Field(example="dog@email.com")
    password: str = Field(min_length=6, example="securepassword")


class SignInSchema(BaseModel):
    identifier: str = Field(example="dog@email.com")
    password: str = Field(example="securepassword")


class AuthResponseSchema(BaseModel):
    message: str
    user_id: int
    username: str | None
    email: str
    palette: list[PaletteColorSchema]
    last_color_id: int
    token: str