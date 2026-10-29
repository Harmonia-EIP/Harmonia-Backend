from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from exceptions.custom_exceptions import HistoryNotFoundException
from models.history import History
from services.history_service import (
    MAX_HISTORY_PER_USER,
    MAX_NAME_LENGTH,
    HistoryService,
)


# =========================
# HELPERS
# =========================


class ChainQuery:
    """Simule la chaîne db.query(...).filter(...).order_by(...)... de SQLAlchemy
    et enregistre les arguments reçus."""

    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value if all_value is not None else []
        self.filter_args = []
        self.order_by_args = None
        self.offset_value = None
        self.delete_calls = []

    def filter(self, *args):
        self.filter_args.append(args)
        return self

    def order_by(self, *args):
        self.order_by_args = args
        return self

    def offset(self, value):
        self.offset_value = value
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        return 0


def make_db(*queries):
    """Chaque appel à db.query(...) renvoie la ChainQuery suivante."""
    db = MagicMock()
    db.query.side_effect = list(queries)
    return db


def filter_map(query):
    """{'user_id': 7, 'id': 5} à partir des expressions passées à .filter()."""
    return {
        expr.left.key: expr.right.value
        for args in query.filter_args
        for expr in args
    }


def purge_db(old_ids):
    """db dont _purge() trouve `old_ids` à supprimer."""
    select_q = ChainQuery(all_value=[SimpleNamespace(id=i) for i in old_ids])
    queries = [select_q]
    delete_q = None
    if old_ids:
        delete_q = ChainQuery()
        queries.append(delete_q)
    return make_db(*queries), select_q, delete_q


OLD = datetime(2020, 1, 1, tzinfo=timezone.utc)


def make_entry(**overrides):
    data = dict(id=5, user_id=7, name="Warm Pad", last_used_at=OLD, created_at=OLD)
    data.update(overrides)
    return SimpleNamespace(**data)


# =========================
# CONSTANTES
# =========================


def test_constants():
    assert MAX_HISTORY_PER_USER == 50
    assert MAX_NAME_LENGTH == 1000


# =========================
# ADD
# =========================


def test_add_returns_the_persisted_entry():
    db, _, _ = purge_db([])

    entry = HistoryService(db).add(7, "Warm Pad", "generate", {"cutoff": 0.5})

    db.add.assert_called_once()
    added = db.add.call_args.args[0]
    assert entry is added
    assert isinstance(entry, History)


def test_add_sets_expected_fields():
    db, _, _ = purge_db([])
    params = {"cutoff": 0.5, "reverb": 0.2}

    entry = HistoryService(db).add(7, "Warm Pad", "generate", params)

    assert entry.user_id == 7
    assert entry.name == "Warm Pad"
    assert entry.type == "generate"
    assert entry.parameters == params


@pytest.mark.parametrize("type_", ["generate", "refine"])
def test_add_keeps_entry_type(type_):
    db, _, _ = purge_db([])

    entry = HistoryService(db).add(1, "x", type_, {})

    assert entry.type == type_


def test_add_accepts_empty_parameters():
    db, _, _ = purge_db([])

    entry = HistoryService(db).add(1, "x", "generate", {})

    assert entry.parameters == {}


def test_add_timestamps_are_utc_aware_and_equal():
    db, _, _ = purge_db([])

    before = datetime.now(timezone.utc)
    entry = HistoryService(db).add(1, "x", "generate", {})
    after = datetime.now(timezone.utc)

    assert entry.created_at == entry.last_used_at
    assert entry.created_at.tzinfo is not None
    assert before <= entry.created_at <= after


@pytest.mark.parametrize(
    "name, expected",
    [
        ("", ""),
        ("short", "short"),
        ("x" * (MAX_NAME_LENGTH - 1), "x" * (MAX_NAME_LENGTH - 1)),
        ("x" * MAX_NAME_LENGTH, "x" * MAX_NAME_LENGTH),
        ("x" * (MAX_NAME_LENGTH + 1), "x" * MAX_NAME_LENGTH),
        ("x" * 5000, "x" * MAX_NAME_LENGTH),
    ],
)
def test_add_truncates_name(name, expected):
    db, _, _ = purge_db([])

    entry = HistoryService(db).add(1, name, "generate", {})

    assert entry.name == expected


def test_add_flushes_then_purges_then_commits_in_one_transaction():
    db, _, _ = purge_db([])

    HistoryService(db).add(1, "x", "generate", {})

    names = [c[0] for c in db.method_calls]
    assert names == ["add", "flush", "query", "commit"]
    db.commit.assert_called_once()


def test_add_with_purge_still_commits_once_at_the_end():
    db, _, _ = purge_db([10, 11])

    HistoryService(db).add(1, "x", "generate", {})

    names = [c[0] for c in db.method_calls]
    assert names == ["add", "flush", "query", "query", "commit"]
    db.commit.assert_called_once()


def test_add_does_not_commit_if_flush_fails():
    db = make_db()
    db.flush.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        HistoryService(db).add(1, "x", "generate", {})

    assert not db.commit.called
    assert not db.query.called  # pas de purge si le flush échoue


def test_add_does_not_commit_if_purge_fails():
    select_q = ChainQuery(all_value=[SimpleNamespace(id=10)])
    delete_q = ChainQuery()
    delete_q.delete = MagicMock(side_effect=RuntimeError("boom"))
    db = make_db(select_q, delete_q)

    with pytest.raises(RuntimeError):
        HistoryService(db).add(1, "x", "generate", {})

    assert not db.commit.called


# ---------- purge (via add) ----------


def test_purge_selects_only_entries_of_this_user():
    db, select_q, _ = purge_db([])

    HistoryService(db).add(42, "x", "generate", {})

    assert filter_map(select_q) == {"user_id": 42}


def test_purge_skips_the_n_most_recent_entries():
    db, select_q, _ = purge_db([])

    HistoryService(db).add(1, "x", "generate", {})

    assert select_q.offset_value == MAX_HISTORY_PER_USER


def test_purge_orders_by_last_used_at_then_id_descending():
    db, select_q, _ = purge_db([])

    HistoryService(db).add(1, "x", "generate", {})

    first, second = select_q.order_by_args
    assert "last_used_at" in str(first) and "DESC" in str(first)
    assert "id" in str(second) and "DESC" in str(second)


def test_purge_does_nothing_when_under_the_limit():
    db, _, delete_q = purge_db([])

    HistoryService(db).add(1, "x", "generate", {})

    assert delete_q is None
    assert db.query.call_count == 1  # seulement le SELECT des ids


@pytest.mark.parametrize("old_ids", [[10], [10, 11, 12], list(range(100, 125))])
def test_purge_deletes_exactly_the_overflowing_ids(old_ids):
    db, _, delete_q = purge_db(old_ids)

    HistoryService(db).add(1, "x", "generate", {})

    (expr,) = delete_q.filter_args[0]
    assert expr.left.key == "id"
    assert list(expr.right.value) == old_ids
    assert delete_q.delete_calls == [{"synchronize_session": False}]


# =========================
# LIST_FOR_USER
# =========================


def test_list_for_user_returns_query_result():
    entries = [make_entry(id=2), make_entry(id=1)]
    q = ChainQuery(all_value=entries)

    res = HistoryService(make_db(q)).list_for_user(7)

    assert res == entries


def test_list_for_user_empty():
    res = HistoryService(make_db(ChainQuery(all_value=[]))).list_for_user(7)

    assert res == []


def test_list_for_user_filters_by_user():
    q = ChainQuery()

    HistoryService(make_db(q)).list_for_user(7)

    assert filter_map(q) == {"user_id": 7}


def test_list_for_user_orders_most_recent_first_with_id_tiebreak():
    q = ChainQuery()

    HistoryService(make_db(q)).list_for_user(7)

    first, second = q.order_by_args
    assert "last_used_at" in str(first) and "DESC" in str(first)
    assert "id" in str(second) and "DESC" in str(second)


def test_list_for_user_does_not_commit():
    db = make_db(ChainQuery())

    HistoryService(db).list_for_user(7)

    assert not db.commit.called


# =========================
# TOUCH
# =========================


def test_touch_updates_last_used_at_and_commits():
    entry = make_entry()
    db = make_db(ChainQuery(first_value=entry))

    before = datetime.now(timezone.utc)
    res = HistoryService(db).touch(7, 5)
    after = datetime.now(timezone.utc)

    assert res is None
    assert before <= entry.last_used_at <= after
    assert entry.last_used_at.tzinfo is not None
    db.commit.assert_called_once()


def test_touch_does_not_change_created_at():
    entry = make_entry()
    db = make_db(ChainQuery(first_value=entry))

    HistoryService(db).touch(7, 5)

    assert entry.created_at == OLD


def test_touch_looks_up_entry_scoped_to_owner():
    q = ChainQuery(first_value=make_entry())

    HistoryService(make_db(q)).touch(user_id=7, entry_id=5)

    assert filter_map(q) == {"id": 5, "user_id": 7}


def test_touch_unknown_or_foreign_entry_raises_not_found():
    db = make_db(ChainQuery(first_value=None))

    with pytest.raises(HistoryNotFoundException):
        HistoryService(db).touch(7, 999)

    assert not db.commit.called


# =========================
# DELETE_ONE
# =========================


def test_delete_one_deletes_entry_and_commits():
    entry = make_entry()
    db = make_db(ChainQuery(first_value=entry))

    res = HistoryService(db).delete_one(7, 5)

    assert res is None
    db.delete.assert_called_once_with(entry)
    db.commit.assert_called_once()


def test_delete_one_deletes_before_commit():
    db = make_db(ChainQuery(first_value=make_entry()))

    HistoryService(db).delete_one(7, 5)

    names = [c[0] for c in db.method_calls]
    assert names == ["query", "delete", "commit"]


def test_delete_one_looks_up_entry_scoped_to_owner():
    q = ChainQuery(first_value=make_entry())

    HistoryService(make_db(q)).delete_one(user_id=7, entry_id=5)

    assert filter_map(q) == {"id": 5, "user_id": 7}


def test_delete_one_unknown_or_foreign_entry_raises_not_found():
    db = make_db(ChainQuery(first_value=None))

    with pytest.raises(HistoryNotFoundException):
        HistoryService(db).delete_one(7, 999)

    assert not db.delete.called
    assert not db.commit.called


# =========================
# CLEAR
# =========================


def test_clear_deletes_all_entries_of_the_user_and_commits():
    q = ChainQuery()
    db = make_db(q)

    res = HistoryService(db).clear(7)

    assert res is None
    assert filter_map(q) == {"user_id": 7}
    assert q.delete_calls == [{"synchronize_session": False}]
    db.commit.assert_called_once()


def test_clear_on_empty_history_does_not_raise():
    q = ChainQuery()
    db = make_db(q)

    HistoryService(db).clear(7)

    db.commit.assert_called_once()


def test_clear_does_not_commit_if_delete_fails():
    q = ChainQuery()
    q.delete = MagicMock(side_effect=RuntimeError("boom"))
    db = make_db(q)

    with pytest.raises(RuntimeError):
        HistoryService(db).clear(7)

    assert not db.commit.called
