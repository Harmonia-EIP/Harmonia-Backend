from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HistoryEntrySchema(BaseModel):
    id: int
    name: str
    type: Literal["generate", "refine"]
    parameters: dict[str, float]
    model_id: str | None = None
    model_name: str | None = None
    created_at: datetime
    last_used_at: datetime