from pydantic import BaseModel
from datetime import datetime

class ProfileSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str
    email: str
    created_at: datetime
    layout_id: int | None = None      # <- layout choisi
    theme_id: int | None = None       # <- thème choisi

    class Config:
        from_attributes = True


class ProfileDetailsSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str
    email: str
    created_at: datetime
    is_active: bool
    role: str | None = None
    layout_id: int | None = None      # <- layout choisi
    theme_id: int | None = None       # <- thème choisi

    class Config:
        from_attributes = True


class UpdateRoleSchema(BaseModel):
    role: str   


class UpdateActiveSchema(BaseModel):
    is_active: bool
