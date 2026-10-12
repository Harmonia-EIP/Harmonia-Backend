from exceptions.custom_exceptions import ErrorCode


def assert_error(res, status_code: int, code: ErrorCode, detail: str | None = None):
    """Vérifie le format d'erreur de l'API : status HTTP + error_code (+ detail)."""
    assert res.status_code == status_code
    body = res.json()
    assert body["error_code"] == code.value
    if detail is not None:
        assert body["detail"] == detail
    else:
        assert isinstance(body["detail"], str)
