from unittest.mock import MagicMock, patch

import pytest

from exceptions.custom_exceptions import (
    InvalidCredentialsException,
    MissingParamException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from models.user import User
from models.user_info import UserInfo
from models.user_params import DEFAULT_LAST_COLOR_ID, DEFAULT_PALETTE, build_palette
from schemas.auth import SignInSchema, SignUpSchema
from services.auth_service import (
    ROLE_ADMIN_ID,
    ROLE_STAFF_ID,
    ROLE_USER_ID,
    AuthService,
)


class DummyInfo:
    def __init__(self, username="maitregims"):
        self.username = username


class DummyParams:
    def __init__(self, palette=None, last_color_id=2):
        self.palette = (
            palette if palette is not None else build_palette(*DEFAULT_PALETTE)
        )
        self.last_color_id = last_color_id


class DummyUser:
    def __init__(
        self,
        user_id=1,
        email="a@b.com",
        password_hash="HASH",
        is_active=True,
        username="maitregims",
    ):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.info = DummyInfo(username=username)
        self.params = DummyParams()


class QueryMock:
    def __init__(self, first_value=None):
        self._first_value = first_value
        self.filters = []
        self.joined = []

    def filter(self, *args, **kwargs):
        self.filters.append(args)
        return self

    def join(self, *args, **kwargs):
        self.joined.append(args)
        return self

    def first(self):
        return self._first_value


def make_db(query_first_map):
    db = MagicMock()
    db.queries = []

    def query_side_effect(model):
        q = QueryMock(first_value=query_first_map.get(model))
        db.queries.append((model, q))
        return q

    db.query.side_effect = query_side_effect
    return db


def payload_signup(
    first_name="maitregims",
    last_name="Artigala",
    username="maitregims",
    email="maitregims@test.com",
    password="securepassword",
):
    return SignUpSchema(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password,
    )


def signup_db(new_id=42):
    db = make_db({User: None, UserInfo: None})

    def flush_side_effect():
        db.add.call_args_list[0].args[0].id = new_id

    db.flush.side_effect = flush_side_effect
    return db


# =========================
# SIGNUP
# =========================


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_success(mock_hash, mock_jwt):
    db = signup_db()
    res = AuthService(db).signup(payload_signup())

    assert res["message"] == "User created successfully"
    assert res["user_id"] == 42
    assert res["username"] == "maitregims"
    assert res["email"] == "maitregims@test.com"
    assert res["token"] == "TOKEN"
    assert "palette" not in res
    assert "last_color_id" not in res
    assert db.commit.called
    assert db.refresh.called


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_persists_expected_objects(mock_hash, mock_jwt):
    db = signup_db(new_id=7)
    AuthService(db).signup(payload_signup())

    user, info, params = [c.args[0] for c in db.add.call_args_list]

    assert isinstance(user, User)
    assert user.email == "maitregims@test.com"
    assert user.password_hash == "HASHED"
    assert user.is_active is True
    assert user.role_id == ROLE_USER_ID

    assert isinstance(info, UserInfo)
    assert info.user_id == 7
    assert info.first_name == "maitregims"
    assert info.last_name == "Artigala"
    assert info.username == "maitregims"

    assert params.user_id == 7
    assert (params.color_1, params.color_2, params.color_3) == tuple(
        DEFAULT_PALETTE[:3]
    )
    assert params.last_color_id == DEFAULT_LAST_COLOR_ID


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_hashes_password_once_and_never_stores_plaintext(mock_hash, mock_jwt):
    db = signup_db()
    AuthService(db).signup(payload_signup(password="securepassword"))

    mock_hash.assert_called_once_with("securepassword")
    user = db.add.call_args_list[0].args[0]
    assert user.password_hash != "securepassword"


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_token_payload(mock_hash, mock_jwt):
    AuthService(signup_db(new_id=5)).signup(payload_signup())
    mock_jwt.assert_called_once_with({"sub": 5})


@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signup_adds_user_info_and_params(mock_jwt, mock_hash):
    db = signup_db()
    AuthService(db).signup(payload_signup())
    assert db.add.call_count == 3
    assert db.flush.called


@pytest.mark.parametrize("field", ["first_name", "last_name", "username"])
@pytest.mark.parametrize("value", ["", "   "])
def test_signup_missing_param_raises(field, value):
    db = make_db({User: None, UserInfo: None})
    with pytest.raises(MissingParamException):
        AuthService(db).signup(payload_signup(**{field: value}))
    assert not db.commit.called


def test_signup_email_already_exists():
    db = make_db({User: DummyUser(), UserInfo: None})
    with pytest.raises(UserAlreadyExistsException):
        AuthService(db).signup(payload_signup(email="exists@test.com"))
    assert not db.add.called
    assert not db.commit.called


def test_signup_username_already_exists():
    db = make_db({User: None, UserInfo: MagicMock()})
    with pytest.raises(UserAlreadyExistsException):
        AuthService(db).signup(payload_signup(username="taken"))
    assert not db.add.called
    assert not db.commit.called


def test_role_constants():
    assert (ROLE_ADMIN_ID, ROLE_STAFF_ID, ROLE_USER_ID) == (1, 2, 3)


# =========================
# SIGNIN
# =========================


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_success_by_email(mock_verify, mock_jwt):
    user = DummyUser(user_id=42, email="test@test.com", username="noe")
    db = make_db({User: user})

    res = AuthService(db).signin(
        SignInSchema(identifier="test@test.com", password="securepassword")
    )

    assert res["message"] == "Login successful"
    assert res["user_id"] == 42
    assert res["email"] == "test@test.com"
    assert res["username"] == "noe"
    assert res["token"] == "TOKEN"
    assert "palette" not in res
    assert "last_color_id" not in res
    mock_verify.assert_called_once_with("securepassword", "HASH")
    # recherche par email : pas de join sur UserInfo
    assert db.queries[0][1].joined == []


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_with_username_uses_join(mock_verify, mock_jwt):
    user = DummyUser(username="noe")
    db = make_db({User: user})

    res = AuthService(db).signin(
        SignInSchema(identifier="noe", password="securepassword")
    )

    assert res["username"] == "noe"
    assert len(db.queries[0][1].joined) == 1


@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_user_not_found(mock_verify):
    db = make_db({User: None})
    with pytest.raises(UserNotFoundException):
        AuthService(db).signin(
            SignInSchema(identifier="test@test.com", password="securepassword")
        )
    mock_verify.assert_not_called()


@patch("services.auth_service.pwd_context.verify", return_value=False)
def test_signin_invalid_password(mock_verify):
    db = make_db({User: DummyUser()})
    with pytest.raises(InvalidCredentialsException):
        AuthService(db).signin(
            SignInSchema(identifier="test@test.com", password="wrong")
        )


@patch("services.auth_service.create_jwt_token")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_inactive_account(mock_verify, mock_jwt):
    db = make_db({User: DummyUser(is_active=False)})
    with pytest.raises(InvalidCredentialsException):
        AuthService(db).signin(
            SignInSchema(identifier="test@test.com", password="securepassword")
        )
    mock_jwt.assert_not_called()


@patch("services.auth_service.pwd_context.verify", return_value=False)
def test_signin_inactive_account_wrong_password_reports_credentials(mock_verify):
    db = make_db({User: DummyUser(is_active=False)})
    with pytest.raises(InvalidCredentialsException):
        AuthService(db).signin(SignInSchema(identifier="test@test.com", password="x"))


@patch("services.auth_service.pwd_context.verify", return_value=True)
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signin_without_user_info(mock_jwt, mock_verify):
    user = DummyUser()
    user.info = None
    res = AuthService(make_db({User: user})).signin(
        SignInSchema(identifier="test@test.com", password="securepassword")
    )
    assert res["username"] is None


@patch("services.auth_service.pwd_context.verify", return_value=True)
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signin_without_params_still_works(mock_jwt, mock_verify):
    user = DummyUser()
    user.params = None
    res = AuthService(make_db({User: user})).signin(
        SignInSchema(identifier="test@test.com", password="securepassword")
    )
    assert res["token"] == "TOKEN"
    assert "palette" not in res
    assert "last_color_id" not in res


@patch("services.auth_service.create_jwt_token")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_jwt_payload(mock_verify, mock_jwt):
    AuthService(make_db({User: DummyUser(user_id=99)})).signin(
        SignInSchema(identifier="test@test.com", password="securepassword")
    )
    mock_jwt.assert_called_once_with({"sub": 99})


@pytest.mark.parametrize("identifier", ["", "@", "unknown", "nobody@nowhere.com"])
def test_signin_unknown_identifiers(identifier):
    with pytest.raises(UserNotFoundException):
        AuthService(make_db({})).signin(
            SignInSchema(identifier=identifier, password="securepassword")
        )
