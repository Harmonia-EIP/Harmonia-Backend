from pydantic import BaseModel


class UpdateLayoutSchema(BaseModel):
    layout_id: int


class UpdateThemeSchema(BaseModel):
    theme_id: int


class UserParamsResponse(BaseModel):
    user_id: int
    layout_id: int
    theme_id: int

    class Config:
        from_attributes = True