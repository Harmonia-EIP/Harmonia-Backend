import re
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from exceptions.custom_exceptions import UserNotFoundException
from services import avatar_service
from services.avatar_service import AvatarService

USER = SimpleNamespace(id=1)


# =========================
# HELPERS / FIXTURES
# =========================


@pytest.fixture(autouse=True)
def storage(tmp_path, monkeypatch):
    """Redirige les uploads vers un dossier temporaire."""
    avatars = tmp_path / "avatars"
    monkeypatch.setattr(avatar_service, "AVATAR_DIR", avatars)
    monkeypatch.setattr(avatar_service, "PUBLIC_BASE_URL", "https://api.test")
    return avatars


def make_image_bytes(fmt="PNG", size=(64, 64), mode="RGB"):
    buf = BytesIO()
    Image.new(mode, size, (200, 30, 30)).save(buf, format=fmt)
    return buf.getvalue()


def upload(data: bytes, name="avatar.png"):
    return UploadFile(file=BytesIO(data), filename=name)


def make_info(avatar_url=None):
    return SimpleNamespace(user_id=1, avatar_url=avatar_url)


def make_db(info):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = info
    return db


def saved_files(storage):
    return list(storage.glob("*")) if storage.exists() else []


# =========================
# set_avatar : succès
# =========================


def test_set_avatar_success(storage):
    info = make_info()
    db = make_db(info)

    url = AvatarService(db).set_avatar(USER, upload(make_image_bytes()))

    assert re.fullmatch(r"https://api\.test/uploads/avatars/1-[0-9a-f]{12}\.png", url)
    assert info.avatar_url == url
    assert db.commit.called

    files = saved_files(storage)
    assert len(files) == 1
    assert files[0].name == url.rsplit("/", 1)[1]


def test_set_avatar_reencodes_to_256_png(storage):
    AvatarService(make_db(make_info())).set_avatar(
        USER, upload(make_image_bytes(size=(400, 100)))
    )

    with Image.open(saved_files(storage)[0]) as img:
        assert img.format == "PNG"
        assert img.size == (256, 256)
        assert img.mode == "RGBA"


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "GIF", "WEBP"])
def test_set_avatar_accepts_allowed_formats(storage, fmt):
    url = AvatarService(make_db(make_info())).set_avatar(
        USER, upload(make_image_bytes(fmt=fmt))
    )
    assert url.endswith(".png")  # toujours réencodé en PNG
    assert len(saved_files(storage)) == 1


def test_set_avatar_ignores_client_filename_and_content_type(storage):
    """Le nom du fichier client ne doit jamais influencer le chemin."""
    url = AvatarService(make_db(make_info())).set_avatar(
        USER, upload(make_image_bytes(), name="../../etc/passwd.exe")
    )
    assert re.search(r"/1-[0-9a-f]{12}\.png$", url)
    assert [f.parent for f in saved_files(storage)] == [storage]


def test_set_avatar_uses_fallback_base_url_when_no_public_url(monkeypatch):
    monkeypatch.setattr(avatar_service, "PUBLIC_BASE_URL", "")

    url = AvatarService(make_db(make_info())).set_avatar(
        USER, upload(make_image_bytes()), fallback_base_url="http://localhost:8000/"
    )

    assert url.startswith("http://localhost:8000/uploads/avatars/1-")


def test_set_avatar_public_base_url_wins_over_fallback():
    url = AvatarService(make_db(make_info())).set_avatar(
        USER, upload(make_image_bytes()), fallback_base_url="http://localhost:8000"
    )
    assert url.startswith("https://api.test/uploads/avatars/1-")


# =========================
# set_avatar : remplacement de l'ancien fichier
# =========================


def test_set_avatar_replaces_and_deletes_old_file(storage):
    info = make_info()
    svc = AvatarService(make_db(info))

    old_url = svc.set_avatar(USER, upload(make_image_bytes()))
    new_url = svc.set_avatar(USER, upload(make_image_bytes()))

    assert old_url != new_url
    names = [f.name for f in saved_files(storage)]
    assert names == [new_url.rsplit("/", 1)[1]]


def test_set_avatar_does_not_delete_file_of_another_user(storage):
    storage.mkdir(parents=True)
    foreign = storage / "99-abcdef123456.png"
    foreign.write_bytes(b"x")
    info = make_info(avatar_url="https://api.test/uploads/avatars/99-abcdef123456.png")

    AvatarService(make_db(info)).set_avatar(USER, upload(make_image_bytes()))

    assert foreign.exists()


def test_set_avatar_commit_failure_rolls_back_and_cleans_up(storage):
    db = make_db(make_info())
    db.commit.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        AvatarService(db).set_avatar(USER, upload(make_image_bytes()))

    db.rollback.assert_called_once()
    assert saved_files(storage) == []


def test_set_avatar_user_info_missing():
    with pytest.raises(UserNotFoundException):
        AvatarService(make_db(None)).set_avatar(USER, upload(make_image_bytes()))


# =========================
# set_avatar : validation du fichier
# =========================


def assert_http_error(exc_info, status):
    assert exc_info.value.status_code == status


def test_set_avatar_empty_file_is_400(storage):
    with pytest.raises(HTTPException) as e:
        AvatarService(make_db(make_info())).set_avatar(USER, upload(b""))
    assert_http_error(e, 400)
    assert saved_files(storage) == []


def test_set_avatar_too_large_is_413(storage):
    too_big = b"x" * (avatar_service.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(HTTPException) as e:
        AvatarService(make_db(make_info())).set_avatar(USER, upload(too_big))
    assert_http_error(e, 413)
    assert saved_files(storage) == []


def test_set_avatar_unsupported_format_is_415(storage):
    with pytest.raises(HTTPException) as e:
        AvatarService(make_db(make_info())).set_avatar(
            USER, upload(make_image_bytes(fmt="BMP"), name="a.png")
        )
    assert_http_error(e, 415)
    assert saved_files(storage) == []


@pytest.mark.parametrize("data", [b"not an image at all", b"\x89PNG\r\n\x1a\n garbage"])
def test_set_avatar_corrupted_is_400(storage, data):
    with pytest.raises(HTTPException) as e:
        AvatarService(make_db(make_info())).set_avatar(USER, upload(data))
    assert_http_error(e, 400)
    assert saved_files(storage) == []


def test_set_avatar_dimensions_too_large_is_400(storage, monkeypatch):
    monkeypatch.setattr(avatar_service, "MAX_SOURCE_PIXELS", 100)
    with pytest.raises(HTTPException) as e:
        AvatarService(make_db(make_info())).set_avatar(
            USER, upload(make_image_bytes(size=(64, 64)))
        )
    assert_http_error(e, 400)
    assert "dimensions" in e.value.detail
    assert saved_files(storage) == []


def test_set_avatar_invalid_image_does_not_touch_db():
    info = make_info(avatar_url="https://api.test/uploads/avatars/1-old.png")
    db = make_db(info)

    with pytest.raises(HTTPException):
        AvatarService(db).set_avatar(USER, upload(b"garbage"))

    assert info.avatar_url == "https://api.test/uploads/avatars/1-old.png"
    assert not db.commit.called


# =========================
# remove_avatar
# =========================


def test_remove_avatar_clears_url_and_deletes_file(storage):
    info = make_info()
    db = make_db(info)
    svc = AvatarService(db)
    svc.set_avatar(USER, upload(make_image_bytes()))
    assert len(saved_files(storage)) == 1

    svc.remove_avatar(USER)

    assert info.avatar_url is None
    assert saved_files(storage) == []
    assert db.commit.call_count == 2  # set + remove


def test_remove_avatar_without_avatar_is_noop():
    info = make_info(avatar_url=None)
    db = make_db(info)

    AvatarService(db).remove_avatar(USER)

    assert info.avatar_url is None
    assert db.commit.called


def test_remove_avatar_user_info_missing():
    with pytest.raises(UserNotFoundException):
        AvatarService(make_db(None)).remove_avatar(USER)


# =========================
# _delete_file
# =========================


def test_delete_file_none_url_is_noop():
    AvatarService(make_db(None))._delete_file(1, None)


def test_delete_file_ignores_foreign_file(storage):
    storage.mkdir(parents=True)
    f = storage / "2-abc.png"
    f.write_bytes(b"x")

    AvatarService(make_db(None))._delete_file(
        1, "https://api.test/uploads/avatars/2-abc.png"
    )

    assert f.exists()


def test_delete_file_blocks_path_traversal(storage, tmp_path):
    """Seul le nom final de l'URL est utilisé : pas de sortie du dossier."""
    storage.mkdir(parents=True)
    outside = tmp_path / "1-secret.png"
    outside.write_bytes(b"x")

    AvatarService(make_db(None))._delete_file(
        1, "https://api.test/uploads/avatars/../../1-secret.png"
    )

    assert outside.exists()


def test_delete_file_swallows_os_errors(monkeypatch):
    fake_dir = MagicMock()
    fake_dir.__truediv__.return_value.unlink.side_effect = OSError("locked")
    monkeypatch.setattr(avatar_service, "AVATAR_DIR", fake_dir)

    AvatarService(make_db(None))._delete_file(
        1, "https://api.test/uploads/avatars/1-abc.png"
    )  # ne doit pas lever
