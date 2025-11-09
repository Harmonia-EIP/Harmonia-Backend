from pydantic import BaseModel
from datetime import datetime

class ProfileSchema(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
