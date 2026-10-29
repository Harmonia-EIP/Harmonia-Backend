from datetime import datetime

from pydantic import BaseModel, Field

from schemas.user_params import PaletteColorSchema
from schemas.history import HistoryEntrySchema


class ProfileSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(example="ano_dev")
    email: str = Field(example="ano@mail.com")
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
