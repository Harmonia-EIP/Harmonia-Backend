from types import SimpleNamespace
from unittest.mock import patch

import pytest

from exceptions.custom_exceptions import (
    ErrorCode,
    HistoryNotFoundException,
    NoPermissionException,
    TokenMissingException,
    UserNotFoundException,
)
from routes.profile import router as profile_router
from tests.helpers import assert_error

# À adapter si le router est monté avec un autre prefix dans main.py
PREFIX = "/profile"

HEADERS = {"Authorization": "Bearer tok"}
CURRENT_USER_ID = 7

# (nom, méthode, url, méthode du HistoryService attendue, args attendus)
ENDPOINTS = [
    ("touch", "POST", "/me/history/5/touch", "touch", (CURRENT_USER_ID, 5)),
    ("delete_one", "DELETE", "/me/history/5", "delete_one", (CURRENT_USER_ID, 5)),
    ("clear", "DELETE", "/me/history", "clear", (CURRENT_USER_ID,)),
]
ENDPOINTS_IDS = [e[0] for e in ENDPOINTS]

# endpoints qui prennent un entry_id (touch / delete_one)
ID_ENDPOINTS = ENDPOINTS[:2]
ID_ENDPOINTS_IDS = ENDPOINTS_IDS[:2]

ALL_SERVICE_METHODS = ["touch", "delete_one", "clear"]


@pytest.fixture()
def client(make_client):
    return make_client(profile_router, prefix=PREFIX)


@pytest.fixture()
def mocks():
    with (
        patch("routes.profile.ProfileService") as profile_cls,
        patch("routes.profile.HistoryService") as history_cls,
    ):
        profile = profile_cls.return_value
        profile.get_current_user.return_value = SimpleNamespace(id=CURRENT_USER_ID)
        yield profile, history_cls.return_value


def call(client, method, url, **kwargs):
    return client.request(method, PREFIX + url, **kwargs)


def assert_no_history_call(history):
    for name in ALL_SERVICE_METHODS:
        getattr(history, name).assert_not_called()


# ---------------- succès ----------------


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_returns_204_with_empty_body(
    client, mocks, _, method, url, svc_method, args
):
    res = call(client, method, url, headers=HEADERS)

    assert res.status_code == 204
    assert res.content == b""


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_calls_service_with_current_user_id(
    client, mocks, _, method, url, svc_method, args
):
    _profile, history = mocks

    call(client, method, url, headers=HEADERS)

    getattr(history, svc_method).assert_called_once_with(*args)


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_only_calls_its_own_service_method(
    client, mocks, _, method, url, svc_method, args
):
    _profile, history = mocks

    call(client, method, url, headers=HEADERS)

    for other in ALL_SERVICE_METHODS:
        if other != svc_method:
            getattr(history, other).assert_not_called()


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_forwards_authorization_header(
    client, mocks, _, method, url, svc_method, args
):
    profile, _history = mocks

    call(client, method, url, headers=HEADERS)

    profile.get_current_user.assert_called_once_with("Bearer tok")


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_uses_user_from_token_not_from_path(
    client, mocks, _, method, url, svc_method, args
):
    profile, history = mocks
    profile.get_current_user.return_value = SimpleNamespace(id=123)

    call(client, method, url, headers=HEADERS)

    assert getattr(history, svc_method).call_args.args[0] == 123


@pytest.mark.parametrize(
    "entry_id", [1, 5, 99999, 0, -3], ids=lambda v: f"id={v}"
)
def test_touch_passes_entry_id_from_path(client, mocks, entry_id):
    _profile, history = mocks

    res = call(client, "POST", f"/me/history/{entry_id}/touch", headers=HEADERS)

    assert res.status_code == 204
    history.touch.assert_called_once_with(CURRENT_USER_ID, entry_id)


@pytest.mark.parametrize(
    "entry_id", [1, 5, 99999, 0, -3], ids=lambda v: f"id={v}"
)
def test_delete_one_passes_entry_id_from_path(client, mocks, entry_id):
    _profile, history = mocks

    res = call(client, "DELETE", f"/me/history/{entry_id}", headers=HEADERS)

    assert res.status_code == 204
    history.delete_one.assert_called_once_with(CURRENT_USER_ID, entry_id)


# ---------------- authentification ----------------


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_requires_auth(
    client, mocks, _, method, url, svc_method, args
):
    profile, history = mocks
    profile.get_current_user.side_effect = TokenMissingException()

    res = call(client, method, url)  # pas de header

    assert_error(res, 401, ErrorCode.TOKEN_MISSING, "Missing token.")
    profile.get_current_user.assert_called_once_with(None)
    assert_no_history_call(history)


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_user_not_found(
    client, mocks, _, method, url, svc_method, args
):
    profile, history = mocks
    profile.get_current_user.side_effect = UserNotFoundException()

    res = call(client, method, url, headers=HEADERS)

    assert_error(res, 404, ErrorCode.USER_NOT_FOUND, "User not found.")
    assert_no_history_call(history)


@pytest.mark.parametrize("_, method, url, svc_method, args", ENDPOINTS, ids=ENDPOINTS_IDS)
def test_history_endpoint_no_permission(
    client, mocks, _, method, url, svc_method, args
):
    profile, history = mocks
    profile.get_current_user.side_effect = NoPermissionException("inactive")

    res = call(client, method, url, headers=HEADERS)

    assert_error(res, 403, ErrorCode.NO_PERMISSION, "inactive")
    assert_no_history_call(history)


# ---------------- erreurs du service ----------------


@pytest.mark.parametrize("_, method, url, svc_method, args", ID_ENDPOINTS, ids=ID_ENDPOINTS_IDS)
def test_history_entry_not_found_is_propagated(
    client, mocks, _, method, url, svc_method, args
):
    _profile, history = mocks
    getattr(history, svc_method).side_effect = HistoryNotFoundException()

    res = call(client, method, url, headers=HEADERS)

    assert_error(res, 404, ErrorCode.HISTORY_NOT_FOUND)


# ---------------- validation des paramètres de chemin ----------------


@pytest.mark.parametrize("_, method, url, svc_method, args", ID_ENDPOINTS, ids=ID_ENDPOINTS_IDS)
@pytest.mark.parametrize("bad_id", ["abc", "1.5", "1e3", "%20"])
def test_history_entry_id_must_be_an_integer(
    client, mocks, _, method, url, svc_method, args, bad_id
):
    _profile, history = mocks
    bad_url = url.replace("/5", f"/{bad_id}")

    res = call(client, method, bad_url, headers=HEADERS)

    assert_error(res, 422, ErrorCode.VALIDATION_ERROR)
    assert_no_history_call(history)


# ---------------- méthodes HTTP / routes inexistantes ----------------


@pytest.mark.parametrize(
    "method, url",
    [
        ("GET", "/me/history/5/touch"),
        ("PUT", "/me/history/5/touch"),
        ("DELETE", "/me/history/5/touch"),
        ("POST", "/me/history/5"),
        ("PUT", "/me/history/5"),
        ("POST", "/me/history"),
        ("PUT", "/me/history"),
    ],
)
def test_history_wrong_method_is_405(client, mocks, method, url):
    _profile, history = mocks

    res = call(client, method, url, headers=HEADERS)

    assert res.status_code == 405
    assert_no_history_call(history)


def test_history_unknown_subroute_is_404(client, mocks):
    res = call(client, "POST", "/me/history/5/nope", headers=HEADERS)

    assert res.status_code == 404
