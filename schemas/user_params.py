from pydantic import BaseModel, Field


class UpdateLayoutSchema(BaseModel):
    layout_id: int = Field(example=1)


class UpdateThemeSchema(BaseModel):
    theme_id: int = Field(example=2)


class UserParamsResponse(BaseModel):
    user_id: int
    layout_id: int
    theme_id: int

    class Config:
        from_attributes = True