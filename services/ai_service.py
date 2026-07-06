import os
import requests
from typing import Optional
from sqlalchemy.orm import Session

from schemas.ai import PresetCharterSchema
from services.profile_service import ProfileService
from exceptions.custom_exceptions import (
    NoUrlForAIConfiguredException,
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

    def call_ai_and_get_patch(
        self,
        prompt: str,
        model_id: int,
        model_name: str
    ) -> Optional[PresetCharterSchema]:

        """Relaie l'appel au serveur Flask IA et renvoie le preset charter brut."""

        if not AI_URL or not AI_URL.strip():
            raise NoUrlForAIConfiguredException()
        print(f"AI_URL: {AI_URL}")
        url = AI_URL.strip()
        body = {"prompt": prompt, "model_id": model_id, "model_name": model_name}
        print(f"Calling AI at {url} with prompt: {prompt}, model_id: {model_id}, model_name: {model_name}")
        try:
            response = requests.post(
                url,
                json=body,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise AiNetworkException(str(exc)) from exc

        if not response.ok:
            raise AiBadStatusException(response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            raise AiInvalidJsonException(str(exc)) from exc

        if not isinstance(data, dict) or "parameters" not in data or "metadata" not in data:
            raise AiInvalidResponseException(
                "Réponse IA invalide : 'metadata' ou 'parameters' manquant."
            )

        try:
            return PresetCharterSchema(**data)
        except Exception as exc:
            raise AiInvalidResponseException(str(exc)) from exc
