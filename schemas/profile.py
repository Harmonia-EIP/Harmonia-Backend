from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from schemas.common import USERNAME_PATTERN, NormalizedEmail, Password
from schemas.history import HistoryEntrySchema
from schemas.user_params import PaletteColorSchema

RoleCode = Literal["ADMIN", "STAFF", "USER"]


class ProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(examples=["ano_dev"])
    email: str = Field(examples=["ano@mail.com"])
    avatar_url: str | None = None
    created_at: datetime
    palette: list[PaletteColorSchema] | None = None
    last_color_id: int | None = None
    history: list[HistoryEntrySchema] = []


class ProfileDetailsSchema(BaseModel):
    """Vue admin d'un compte (sans l'historique)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(examples=["ano_dev"])
    email: str = Field(examples=["ano@mail.com"])
    avatar_url: str | None = None
    created_at: datetime
    is_active: bool
    role: RoleCode | None = Field(examples=["ADMIN"])
    palette: list[PaletteColorSchema] | None = None
    last_color_id: int | None = None


class UpdateRoleSchema(BaseModel):
    role: RoleCode = Field(examples=["ADMIN"])

    @field_validator("role", mode="before")
    @classmethod
    def normalize(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class UpdateActiveSchema(BaseModel):
    is_active: bool


# ---------------------------------------------------------------------------
# Mise à jour du compte
# ---------------------------------------------------------------------------
class UpdateProfileSchema(BaseModel):
    """PATCH /profile/me : seuls les champs envoyés sont modifiés.
    L'avatar ne se change pas ici : voir POST /profile/me/avatar."""

    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str | None = Field(
        default=None, min_length=1, max_length=50, examples=["Damien"]
    )
    last_name: str | None = Field(
        default=None, min_length=1, max_length=50, examples=["Chien"]
    )
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=USERNAME_PATTERN,
        examples=["dogMAN"],
    )

    @model_validator(mode="after")
    def check_content(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field")

        for name in ("first_name", "last_name", "username"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"'{name}' cannot be null")

        return self


class UpdateEmailSchema(BaseModel):
    new_email: NormalizedEmail = Field(examples=["new@email.com"])
    current_password: str = Field(max_length=1024, examples=["securepassword"])


class UpdatePasswordSchema(BaseModel):
    current_password: str = Field(max_length=1024, examples=["oldpassword"])
    new_password: Password = Field(examples=["newsecurepassword"])

    @model_validator(mode="after")
    def check_different(self):
        if self.new_password == self.current_password:
            raise ValueError("New password must be different from the current one")
        return self


class PasswordChangedSchema(BaseModel):
    """Les anciens tokens sont révoqués : le client doit garder celui-ci."""

    message: str = "Password updated"
    token: str


class AvatarResponseSchema(BaseModel):
    avatar_url: str | None = None
