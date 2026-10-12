from pydantic import BaseModel, Field, model_validator

HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class PaletteColorSchema(BaseModel):
    id: int = Field(ge=1, le=3, example=2)
    color: str = Field(pattern=HEX_COLOR_PATTERN, example="#CBA6F7")


class UpdatePaletteSchema(BaseModel):
    """Tout est optionnel, mais il faut au moins un des deux champs."""

    colors: list[PaletteColorSchema] | None = Field(
        default=None, example=[{"id": 2, "color": "#CBA6F7"}]
    )
    last_color_id: int | None = Field(default=None, ge=1, le=3, example=2)

    @model_validator(mode="after")
    def check_content(self):
        if self.colors is None and self.last_color_id is None:
            raise ValueError("Provide 'colors' and/or 'last_color_id'")
        if self.colors:
            ids = [c.id for c in self.colors]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate color id")
        return self


class UserParamsResponse(BaseModel):
    user_id: int
    palette: list[PaletteColorSchema]
    last_color_id: int

    class Config:
        from_attributes = True
