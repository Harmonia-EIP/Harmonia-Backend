from datetime import datetime, timezone

from sqlalchemy.orm import Session

from exceptions.custom_exceptions import HistoryNotFoundException
from models.history import History

MAX_HISTORY_PER_USER = 50
MAX_NAME_LENGTH = 1000
MAX_MODEL_ID_LENGTH = 100
MAX_MODEL_NAME_LENGTH = 200


def _clip(value: int | str | None, max_len: int) -> str | None:
    """Convertit en texte, tronque, et renvoie None si vide."""
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_len] if text else None


class HistoryService:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        user_id: int,
        name: str,
        type_: str,
        parameters: dict[str, float],
        model_id: int | str | None = None,
        model_name: str | None = None,
    ) -> History:
        """Insertion + purge dans la même transaction."""
        now = datetime.now(timezone.utc)
        entry = History(
            user_id=user_id,
            name=name[:MAX_NAME_LENGTH],
            type=type_,
            parameters=parameters,
            model_id=_clip(model_id, MAX_MODEL_ID_LENGTH),
            model_name=_clip(model_name, MAX_MODEL_NAME_LENGTH),
            created_at=now,
            last_used_at=now,
        )
        self.db.add(entry)
        self.db.flush()
        self._purge(user_id)
        self.db.commit()
        return entry

    def list_for_user(self, user_id: int) -> list[History]:
        return (
            self.db.query(History)
            .filter(History.user_id == user_id)
            .order_by(History.last_used_at.desc(), History.id.desc())
            .all()
        )

    def touch(self, user_id: int, entry_id: int) -> None:
        """Remonte l'entrée en tête de liste (chargée par l'utilisateur)."""
        entry = self._get_owned(user_id, entry_id)
        entry.last_used_at = datetime.now(timezone.utc)
        self.db.commit()

    def delete_one(self, user_id: int, entry_id: int) -> None:
        entry = self._get_owned(user_id, entry_id)
        self.db.delete(entry)
        self.db.commit()

    def clear(self, user_id: int) -> None:
        self.db.query(History).filter(History.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db.commit()

    # ------------------------------------------------------------------
    def _get_owned(self, user_id: int, entry_id: int) -> History:
        entry = (
            self.db.query(History)
            .filter(History.id == entry_id, History.user_id == user_id)
            .first()
        )
        if not entry:
            raise HistoryNotFoundException()
        return entry

    def _purge(self, user_id: int) -> None:
        """Supprime tout ce qui dépasse les N plus récentes de cet utilisateur."""
        old_ids = [
            row.id
            for row in self.db.query(History.id)
            .filter(History.user_id == user_id)
            .order_by(History.last_used_at.desc(), History.id.desc())
            .offset(MAX_HISTORY_PER_USER)
            .all()
        ]
        if old_ids:
            self.db.query(History).filter(History.id.in_(old_ids)).delete(
                synchronize_session=False
            )