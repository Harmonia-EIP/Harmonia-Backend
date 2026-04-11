import pytest
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from schemas.auth import SignUpSchema, SignInSchema
from exceptions.custom_exceptions import (
    MissingParamException,
    UserAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException,
)


class DummyInfo:
    def __init__(self, username="maitregims"):
        self.username = username


class DummyParams:
    def __init__(self, layout_id=1, theme_id=1):
        self.layout_id = layout_id
        self.theme_id = theme_id


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

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value


def make_db(query_first_map):
    db = MagicMock()

    def query_side_effect(model):
        return QueryMock(first_value=query_first_map.get(model))

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


# =========================
# SIGNUP TESTS
# =========================

@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_success(mock_hash, mock_jwt):
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: None,
        UserInfo: None,
    })

    def flush_side_effect():
        user_obj = db.add.call_args_list[0].args[0]
        user_obj.id = 42

    db.flush.side_effect = flush_side_effect

    service = AuthService(db)
    res = service.signup(payload_signup())

    assert res["message"] == "Utilisateur créé avec succès"
    assert res["user_id"] == 42
    assert res["token"] == "TOKEN"
    assert db.commit.called
    assert db.refresh.called


def test_signup_missing_param_raises():
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: None,
        UserInfo: None,
    })

    service = AuthService(db)

    with pytest.raises(MissingParamException):
        service.signup(payload_signup(first_name=""))


def test_signup_email_already_exists():
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: DummyUser(),
        UserInfo: None,
    })

    service = AuthService(db)

    with pytest.raises(UserAlreadyExistsException):
        service.signup(payload_signup(email="exists@test.com"))


def test_signup_username_already_exists():
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: None,
        UserInfo: MagicMock(),
    })

    service = AuthService(db)

    with pytest.raises(UserAlreadyExistsException):
        service.signup(payload_signup(username="taken"))


@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signup_calls_hash(mock_jwt, mock_hash):
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: None,
        UserInfo: None,
    })

    def flush_side_effect():
        db.add.call_args_list[0].args[0].id = 1

    db.flush.side_effect = flush_side_effect

    service = AuthService(db)
    service.signup(payload_signup())

    mock_hash.assert_called_once()


def test_signup_creates_objects():
    from models.user import User
    from models.user_info import UserInfo

    db = make_db({
        User: None,
        UserInfo: None,
    })

    def flush_side_effect():
        db.add.call_args_list[0].args[0].id = 1

    db.flush.side_effect = flush_side_effect

    service = AuthService(db)
    service.signup(payload_signup())

    # user + info + params
    assert db.add.call_count >= 3


# =========================
# SIGNIN TESTS
# =========================

@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_success_by_email(mock_verify, mock_jwt):
    from models.user import User

    user = DummyUser(user_id=42, email="test@test.com", username="noe")

    db = make_db({User: user})

    service = AuthService(db)
    res = service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))

    assert res["message"] == "Connexion réussie"
    assert res["user_id"] == 42
    assert res["email"] == "test@test.com"
    assert res["username"] == "noe"
    assert res["token"] == "TOKEN"


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_with_username(mock_verify, mock_jwt):
    from models.user import User

    user = DummyUser(username="noe")

    db = make_db({User: user})

    service = AuthService(db)
    res = service.signin(SignInSchema(identifier="noe", password="securepassword"))

    assert res["username"] == "noe"


@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_user_not_found(mock_verify):
    from models.user import User

    db = make_db({User: None})

    service = AuthService(db)

    with pytest.raises(UserNotFoundException):
        service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))


@patch("services.auth_service.pwd_context.verify", return_value=False)
def test_signin_invalid_password(mock_verify):
    from models.user import User

    db = make_db({User: DummyUser()})

    service = AuthService(db)

    with pytest.raises(InvalidCredentialsException):
        service.signin(SignInSchema(identifier="test@test.com", password="wrong"))


@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_inactive_account(mock_verify):
    from models.user import User

    user = DummyUser(is_active=False)

    db = make_db({User: user})

    service = AuthService(db)

    with pytest.raises(InvalidCredentialsException):
        service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))


@patch("services.auth_service.pwd_context.verify", return_value=True)
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signin_without_user_info(mock_jwt, mock_verify):
    from models.user import User

    user = DummyUser()
    user.info = None

    db = make_db({User: user})

    service = AuthService(db)
    res = service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))

    assert res["username"] is None


@patch("services.auth_service.pwd_context.verify", return_value=True)
@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
def test_signin_without_user_params(mock_jwt, mock_verify):
    from models.user import User

    user = DummyUser()
    user.params = None

    db = make_db({User: user})

    service = AuthService(db)
    res = service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))

    assert res["layout_id"] == 1
    assert res["theme_id"] == 1


@patch("services.auth_service.create_jwt_token")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_jwt_payload(mock_verify, mock_jwt):
    from models.user import User

    user = DummyUser(user_id=99)

    db = make_db({User: user})

    service = AuthService(db)
    service.signin(SignInSchema(identifier="test@test.com", password="securepassword"))

    mock_jwt.assert_called_once_with({"sub": 99})


def test_signin_empty_identifier():
    service = AuthService(make_db({}))

    with pytest.raises(UserNotFoundException):
        service.signin(SignInSchema(identifier="", password="securepassword"))


def test_signin_identifier_edge_case():
    service = AuthService(make_db({}))

    with pytest.raises(UserNotFoundException):
        service.signin(SignInSchema(identifier="@", password="securepassword"))