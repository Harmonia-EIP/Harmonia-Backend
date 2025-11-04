from pydantic import BaseModel
from typing import Any, Optional

class ApiResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Optional[Any] = None
