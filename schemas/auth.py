from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from schemas.common import USERNAME_PATTERN, NormalizedEmail, Password
from schemas.user_params import PaletteColorSchema

# Champs vides acceptés ici : AuthService renvoie alors MISSING_PARAM.
SignUpName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
SignUpUsername = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=30,
        pattern=r"^(?:[A-Za-z0-9_.-]{3,30})?$",
    ),
]


class SignUpSchema(BaseModel):
    first_name: SignUpName = Field(examples=["Damien"])
    last_name: SignUpName = Field(examples=["Chien"])
    username: SignUpUsername = Field(
        examples=["dogMAN"],
        description=f"3 à 30 caractères, {USERNAME_PATTERN}",
    )
    email: NormalizedEmail = Field(examples=["dog@email.com"])
    password: Password = Field(examples=["securepassword"])


class SignInSchema(BaseModel):
    identifier: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=320)
    ] = Field(examples=["dog@email.com"])
    password: Annotated[str, StringConstraints(max_length=1024)] = Field(
        examples=["securepassword"]
    )


class AuthResponseSchema(BaseModel):
    message: str
    user_id: int
    username: str | None
    email: str
    token: str
    palette: list[PaletteColorSchema] | None = None
    last_color_id: int | None = None
    avatar_url: str | None = None
