import os
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import UserNotFoundException
from models.user_info import UserInfo

# Dossier des fichiers envoyés : doit être un VOLUME Docker en production.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
AVATAR_DIR = UPLOAD_DIR / "avatars"

# URL publique de l'API, telle que le plugin et le site la voient
# (ex. https://api.mon-domaine.com). Vide : repli sur l'URL de la requête (dev local).
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SOURCE_PIXELS = 25_000_000
AVATAR_SIZE = 256
ALLOWED_FORMATS = {"PNG", "JPEG", "GIF", "WEBP"}


class AvatarService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    def set_avatar(self, user, file: UploadFile, fallback_base_url: str = "") -> str:
        """Valide l'image, la réencode en PNG 256x256, l'enregistre sur disque
        et met à jour avatar_url. Supprime l'ancien fichier. Renvoie l'URL."""

        info = self._get_info(user.id)
        png = self._process(file)

        base = (PUBLIC_BASE_URL or fallback_base_url).rstrip("/")

        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{user.id}-{uuid.uuid4().hex[:12]}.png"  # nom choisi par nous, jamais par le client
        path = AVATAR_DIR / name
        path.write_bytes(png)

        old_url = info.avatar_url
        info.avatar_url = f"{base}/uploads/avatars/{name}"

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            path.unlink(missing_ok=True)
            raise

        self._delete_file(user.id, old_url)
        return info.avatar_url

    def remove_avatar(self, user) -> None:
        info = self._get_info(user.id)
        old_url = info.avatar_url

        info.avatar_url = None
        self.db.commit()

        self._delete_file(user.id, old_url)

    # ------------------------------------------------------------------
    def _get_info(self, user_id: int) -> UserInfo:
        info = self.db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
        if not info:
            raise UserNotFoundException()
        return info

    def _process(self, file: UploadFile) -> bytes:
        # On ne fait confiance ni au nom ni au Content-Type : Pillow décide.
        data = file.file.read(MAX_UPLOAD_BYTES + 1)

        if not data:
            raise HTTPException(status_code=400, detail="Empty file")
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 2 MB)")

        try:
            img = Image.open(BytesIO(data))  # lecture paresseuse

            if img.format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Unsupported image format (use PNG, JPEG, GIF or WebP)",
                )
            if img.width * img.height > MAX_SOURCE_PIXELS:
                raise HTTPException(
                    status_code=400, detail="Image dimensions too large"
                )

            img.load()
            img = ImageOps.exif_transpose(img)
            img = ImageOps.fit(
                img.convert("RGBA"),
                (AVATAR_SIZE, AVATAR_SIZE),
                Image.Resampling.LANCZOS,
            )
        except HTTPException:
            raise
        except Exception:  # noqa: BLE001  Pillow lève des erreurs variées (OSError, SyntaxError, ValueError, EOFError...) sur un fichier corrompu
            raise HTTPException(
                status_code=400, detail="Invalid or corrupted image"
            ) from None
        out = BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()

    def _delete_file(self, user_id: int, url: str | None) -> None:
        """Supprime l'ancien fichier, uniquement s'il appartient bien à cet utilisateur."""
        if not url:
            return

        name = Path(urlparse(url).path).name

        if not name.startswith(f"{user_id}-"):
            return

        try:
            (AVATAR_DIR / name).unlink(missing_ok=True)
        except OSError:
            pass
