from pydantic import BaseModel, Field
from datetime import datetime


class ProfileSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str = Field(example="ano_dev")
    email: str = Field(example="ano@mail.com")
    created_at: datetime
    layout_id: int | None = None
    theme_id: int | None = None

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
    layout_id: int | None = None
    theme_id: int | None = None

    class Config:
        from_attributes = True


class UpdateRoleSchema(BaseModel):
    role: str = Field(example="ADMIN")


class UpdateActiveSchema(BaseModel):
    is_active: bool