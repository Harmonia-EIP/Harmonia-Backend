from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from schemas.history import HistoryEntrySchema
from schemas.user_params import PaletteColorSchema


class ProfileSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(example="ano_dev")
    email: str = Field(example="ano@mail.com")
    avatar_url: str | None = None
    created_at: datetime
    palette: list[PaletteColorSchema] | None = None
    last_color_id: int | None = None
    history: list[HistoryEntrySchema] = []

    class Config:
        from_attributes = True


class ProfileDetailsSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(example="ano_dev")
    email: str = Field(example="ano@mail.com")
    avatar_url: str | None = None
    created_at: datetime
    is_active: bool
    role: str | None = Field(example="ADMIN")
    palette: list[PaletteColorSchema] | None = None
    last_color_id: int | None = None
    history: list[HistoryEntrySchema] = []

    class Config:
        from_attributes = True


class UpdateRoleSchema(BaseModel):
    role: str = Field(example="ADMIN")


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
        default=None, min_length=1, max_length=50, example="Damien"
    )
    last_name: str | None = Field(
        default=None, min_length=1, max_length=50, example="Chien"
    )
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_.-]+$",
        example="dogMAN",
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
    new_email: EmailStr = Field(example="new@email.com")
    current_password: str = Field(example="securepassword")


class UpdatePasswordSchema(BaseModel):
    current_password: str = Field(example="oldpassword")
    new_password: str = Field(min_length=6, max_length=72, example="newsecurepassword")

    @model_validator(mode="after")
    def check_different(self):
        if self.new_password == self.current_password:
            raise ValueError("New password must be different from the current one")
        return self


class AvatarResponseSchema(BaseModel):
    avatar_url: str | None = None
