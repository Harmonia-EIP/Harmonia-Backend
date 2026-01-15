import pytest
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from schemas.auth import SignUpSchema, SignInSchema
from exceptions.custom_exceptions import (
    MissingParamException,
    UserAlreadyExistsException,
    NoRoleSeedsInDatabaseException,
    UserNotFoundException,
    InvalidCredentialsException,
)


class DummyInfo:
    def __init__(self, username="maitregims"):
        self.username = username


class DummyUser:
    def __init__(self, user_id=1, email="a@b.com", password_hash="HASH", is_active=True, username="maitregims"):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.info = DummyInfo(username=username)


class DummyRole:
    def __init__(self, role_id=1, code="USER"):
        self.id = role_id
        self.code = code


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
    """
    query_first_map: dict[type, Any]
      ex: {User: None, UserInfo: None, Role: DummyRole(), UserRole: None}
    """
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
    password="1234",
):
    return SignUpSchema(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password,
    )


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.hash", return_value="HASHED")
def test_signup_success(mock_hash, mock_jwt):
    from services.auth_service import User, UserInfo, Role, UserRole  # modèles importés dans le module

    role_user = DummyRole(role_id=7, code="USER")
    db = make_db({
        User: None,        # email pas pris
        UserInfo: None,    # username pas pris
        Role: role_user,   # rôle USER existe
        UserRole: None,
    })

    # flush doit donner un id à l'user créé
    def flush_side_effect():
        # le 1er add est User(...)
        # on récupère l'objet ajouté et on lui met un id
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
    from services.auth_service import User, UserInfo, Role, UserRole

    db = make_db({User: None, UserInfo: None, Role: DummyRole(), UserRole: None})
    service = AuthService(db)

    bad_payload = payload_signup(first_name="")  # vide => MissingParamException

    with pytest.raises(MissingParamException) as exc:
        service.signup(bad_payload)

    assert exc.value.status_code == 400


def test_signup_email_already_exists():
    from services.auth_service import User, UserInfo, Role, UserRole

    db = make_db({
        User: DummyUser(),  # email déjà utilisé
        UserInfo: None,
        Role: DummyRole(),
        UserRole: None,
    })
    service = AuthService(db)

    with pytest.raises(UserAlreadyExistsException) as exc:
        service.signup(payload_signup(email="exists@test.com"))

    assert exc.value.status_code == 409


def test_signup_username_already_exists():
    from services.auth_service import User, UserInfo, Role, UserRole

    # email libre mais username pris
    db = make_db({
        User: None,
        UserInfo: MagicMock(),  # username existe déjà
        Role: DummyRole(),
        UserRole: None,
    })
    service = AuthService(db)

    with pytest.raises(UserAlreadyExistsException) as exc:
        service.signup(payload_signup(username="taken"))

    assert exc.value.status_code == 409


def test_signup_role_user_missing_seed():
    from services.auth_service import User, UserInfo, Role, UserRole

    db = make_db({
        User: None,
        UserInfo: None,
        Role: None,  # rôle USER manquant
        UserRole: None,
    })

    def flush_side_effect():
        user_obj = db.add.call_args_list[0].args[0]
        user_obj.id = 1

    db.flush.side_effect = flush_side_effect

    service = AuthService(db)

    with pytest.raises(NoRoleSeedsInDatabaseException) as exc:
        service.signup(payload_signup())

    assert exc.value.status_code == 500


@patch("services.auth_service.create_jwt_token", return_value="TOKEN")
@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_success_by_email(mock_verify, mock_jwt):
    from services.auth_service import User, UserInfo, Role, UserRole

    user = DummyUser(user_id=42, email="test@test.com", username="noe", is_active=True)

    db = make_db({
        User: user,   # query(User).filter(User.email==...).first() => user
        UserInfo: None,
        Role: None,
        UserRole: None,
    })

    service = AuthService(db)
    res = service.signin(SignInSchema(identifier="test@test.com", password="1234"))

    assert res["message"] == "Connexion réussie"
    assert res["user_id"] == 42
    assert res["email"] == "test@test.com"
    assert res["username"] == "noe"
    assert res["token"] == "TOKEN"


@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_user_not_found(mock_verify):
    from services.auth_service import User, UserInfo, Role, UserRole

    db = make_db({User: None, UserInfo: None, Role: None, UserRole: None})
    service = AuthService(db)

    with pytest.raises(UserNotFoundException) as exc:
        service.signin(SignInSchema(identifier="test@test.com", password="1234"))

    assert exc.value.status_code == 404


@patch("services.auth_service.pwd_context.verify", return_value=False)
def test_signin_invalid_password(mock_verify):
    from services.auth_service import User, UserInfo, Role, UserRole

    db = make_db({User: DummyUser(), UserInfo: None, Role: None, UserRole: None})
    service = AuthService(db)

    with pytest.raises(InvalidCredentialsException) as exc:
        service.signin(SignInSchema(identifier="test@test.com", password="bad"))

    assert exc.value.status_code == 401


@patch("services.auth_service.pwd_context.verify", return_value=True)
def test_signin_inactive_account(mock_verify):
    from services.auth_service import User, UserInfo, Role, UserRole

    user = DummyUser(is_active=False)
    db = make_db({User: user, UserInfo: None, Role: None, UserRole: None})
    service = AuthService(db)

    with pytest.raises(InvalidCredentialsException) as exc:
        service.signin(SignInSchema(identifier="test@test.com", password="1234"))

    assert exc.value.status_code == 401
