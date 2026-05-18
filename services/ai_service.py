import os
import requests
from typing import Dict, Any
from sqlalchemy.orm import Session

from services.profile_service import ProfileService
from exceptions.custom_exceptions import (
    AiNetworkException,
    AiBadStatusException,
    AiInvalidJsonException,
    AiInvalidResponseException,
)

AI_URL = os.getenv("AI_URL")


class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)

    def call_ai_and_get_patch(self, prompt: str) -> Dict[str, Any]:

        if not AI_URL or not AI_URL.strip():
            raise AiInvalidResponseException("AI_URL not configured")

        try:
            response = requests.post(
                AI_URL.strip(),
                json={"prompt": prompt},
                timeout=15
            )

        except requests.RequestException as exc:
            raise AiNetworkException(str(exc)) from exc

        if not response.ok:
            raise AiBadStatusException(response.status_code)

        try:
            data = response.json()

        except ValueError as exc:
            raise AiInvalidJsonException(str(exc)) from exc

        if "parameters" not in data:
            raise AiInvalidResponseException(
                "Missing 'parameters' field"
            )

        return data