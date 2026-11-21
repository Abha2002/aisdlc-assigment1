"""Contract tests derived from spec requirements FR-1..FR-11 and NFR-6.

Each test name carries the requirement id it verifies (test_frN_...).
"""
import json
import os
from datetime import datetime

import pytest

from todo.errors import (
    InvalidTransitionError,
    StorageError,
    TaskNotFoundError,
    TodoError,
    ValidationError,
)
from todo.service import TaskService

TASK_KEYS = {"id", "title", "priority", "status", "tags", "created_at"}


# ---------------------------------------------------------------- FR-1 create
def test_fr1_add_returns_exact_schema_and_defaults(svc):
    t = svc.add_task("Buy milk")
    assert set(t) == TASK_KEYS
    assert t["id"] == 1
    assert t["title"] == "Buy milk"
    assert t["priority"] == "medium"
    assert t["status"] == "todo"
    assert t["tags"] == []
    assert datetime.fromisoformat(t["created_at"]).tzinfo is not None


def test_fr1_ids_increment_from_one(svc):
    assert [svc.add_task(f"t{i}")["id"] for i in range(3)] == [1, 2, 3]


# ---------------------------------------------------------------- FR-2 title
@pytest.mark.parametrize("bad", ["", "   ", "x" * 101, None, 123, ["a"]])
def test_fr2_invalid_title_rejected(svc, bad):
    with pytest.raises(ValidationError):
        svc.add_task(bad)


def test_fr2_title_trimmed_and_100_chars_allowed(svc):
    assert svc.add_task("  padded  ")["title"] == "padded"
    assert len(svc.add_task("  " + "x" * 100 + "  ")["title"]) == 100


def test_fr2_failed_add_does_not_consume_id(svc):
    with pytest.raises(ValidationError):
        svc.add_task("")
    assert svc.add_task("ok")["id"] == 1


# ------------------------------------------------------------- FR-3 priority
@pytest.mark.parametrize("bad", ["urgent", "HIGH", "", 1])
def test_fr3_invalid_priority_rejected(svc, bad):
    with pytest.raises(ValidationError):
        svc.add_task("a", priority=bad)


@pytest.mark.parametrize("p", ["low", "medium", "high"])
def test_fr3_valid_priorities(svc, p):
    assert svc.add_task("a", priority=p)["priority"] == p


# ------------------------------------------------------------------ FR-4 tags
def test_fr4_tags_normalised_and_deduplicated_in_order(svc):
    t = svc.add_task("a", tags=[" Work ", "home", "WORK", "home"])
    assert t["tags"] == ["work", "home"]


@pytest.mark.parametrize("bad", ["bad tag", "a_b", "x" * 21, "", "  ", "tag!"])
def test_fr4_invalid_tag_rejected(svc, bad):
    with pytest.raises(ValidationError):
        svc.add_task("a", tags=[bad])


def test_fr4_max_ten_distinct_tags(svc):
    assert len(svc.add_task("a", tags=[f"t{i}" for i in range(10)])["tags"]) == 10
    with pytest.raises(ValidationError):
        svc.add_task("a", tags=[f"t{i}" for i in range(11)])


@pytest.mark.parametrize("bad", ["work", 5, [1], [None]])
def test_fr4_tags_must_be_list_of_strings(svc, bad):
    with pytest.raises(ValidationError):
        svc.add_task("a", tags=bad)


# --------------------------------------------------------------------- FR-5 get
def test_fr5_get_returns_task(svc):
    svc.add_task("a")
    assert svc.get_task(1)["title"] == "a"


@pytest.mark.parametrize("missing", [0, -1, 99])
def test_fr5_get_missing_raises_not_found(svc, missing):
    with pytest.raises(TaskNotFoundError):
        svc.get_task(missing)


@pytest.mark.parametrize("bad", ["1", True, 1.0, None])
def test_fr5_non_integer_id_is_validation_error(svc, bad):
    svc.add_task("a")
    with pytest.raises(ValidationError):
        svc.get_task(bad)


# ------------------------------------------------------------------ FR-6 update
def test_fr6_update_fields_independently(svc):
    svc.add_task("a", priority="low", tags=["x"])
    t = svc.update_task(1, title="b")
    assert (t["title"], t["priority"], t["tags"]) == ("b", "low", ["x"])
    t = svc.update_task(1, priority="high")
    assert (t["title"], t["priority"], t["tags"]) == ("b", "high", ["x"])
    t = svc.update_task(1, tags=["Y", "z"])
    assert t["tags"] == ["y", "z"]


def test_fr6_empty_list_clears_tags(svc):
    svc.add_task("a", tags=["x"])
    assert svc.update_task(1, tags=[])["tags"] == []


def test_fr6_update_does_not_touch_status_or_created_at(svc):
    created = svc.add_task("a")
    svc.set_status(1, "in_progress")
    t = svc.update_task(1, title="b")
    assert t["status"] == "in_progress"
    assert t["created_at"] == created["created_at"]


def test_fr6_update_with_no_fields_is_validation_error(svc):
    svc.add_task("a")
    with pytest.raises(ValidationError):
        svc.update_task(1)


def test_fr6_invalid_update_leaves_task_unchanged(svc):
    svc.add_task("a", priority="low")
    with pytest.raises(ValidationError):
        svc.update_task(1, title="new", priority="bogus")
    t = svc.get_task(1)
    assert (t["title"], t["priority"]) == ("a", "low")


def test_fr6_update_missing_task(svc):
    with pytest.raises(TaskNotFoundError):
        svc.update_task(5, title="x")


# ------------------------------------------------------------------ FR-7 delete
def test_fr7_delete_removes_task(svc):
    svc.add_task("a")
    assert svc.delete_task(1) is None
    with pytest.raises(TaskNotFoundError):
        svc.get_task(1)
    assert svc.list_tasks() == []


def test_fr7_ids_are_never_reused(svc):
    svc.add_task("a")
    svc.add_task("b")
    svc.delete_task(2)
    assert svc.add_task("c")["id"] == 3


def test_fr7_delete_missing_raises(svc):
    with pytest.raises(TaskNotFoundError):
        svc.delete_task(1)


# ------------------------------------------------------------- FR-8 transitions
ALLOWED = [
    ("todo", "in_progress"),
    ("todo", "done"),
    ("in_progress", "todo"),
    ("in_progress", "done"),
    ("done", "todo"),
]
FORBIDDEN = [
    ("todo", "todo"),
    ("in_progress", "in_progress"),
    ("done", "done"),
    ("done", "in_progress"),
]
PATHS = {"todo": [], "in_progress": ["in_progress"], "done": ["done"]}


def _bring_to(svc, state):
    svc.add_task("a")
    for step in PATHS[state]:
        svc.set_status(1, step)


@pytest.mark.parametrize(("src", "dst"), ALLOWED)
def test_fr8_allowed_transitions(svc, src, dst):
    _bring_to(svc, src)
    assert svc.set_status(1, dst)["status"] == dst
    assert svc.get_task(1)["status"] == dst


@pytest.mark.parametrize(("src", "dst"), FORBIDDEN)
def test_fr8_forbidden_transitions_raise_and_do_not_change_state(svc, src, dst):
    _bring_to(svc, src)
    with pytest.raises(InvalidTransitionError):
        svc.set_status(1, dst)
    assert svc.get_task(1)["status"] == src


@pytest.mark.parametrize("bad", ["archived", "DONE", "", None])
def test_fr8_unknown_status_is_validation_error(svc, bad):
    svc.add_task("a")
    with pytest.raises(ValidationError):
        svc.set_status(1, bad)


def test_fr8_status_on_missing_task(svc):
    with pytest.raises(TaskNotFoundError):
        svc.set_status(1, "done")


# ----------------------------------------------------------------- FR-9 listing
def _seed(svc):
    svc.add_task("a", priority="low", tags=["work"])  # 1
    svc.add_task("b", priority="high", tags=["home"])  # 2
    svc.add_task("c", priority="medium", tags=["Work"])  # 3
    svc.add_task("d", priority="high", tags=["work", "home"])  # 4
    svc.set_status(4, "done")


def test_fr9_default_sort_is_priority_then_id(svc):
    _seed(svc)
    assert [t["id"] for t in svc.list_tasks()] == [2, 4, 3, 1]


def test_fr9_sort_by_id(svc):
    _seed(svc)
    assert [t["id"] for t in svc.list_tasks(sort="id")] == [1, 2, 3, 4]


def test_fr9_tag_filter_is_case_insensitive(svc):
    _seed(svc)
    assert [t["id"] for t in svc.list_tasks(tag="WORK")] == [4, 3, 1]
    assert svc.list_tasks(tag="nothing") == []


def test_fr9_status_filter_and_combination(svc):
    _seed(svc)
    assert [t["id"] for t in svc.list_tasks(status="done")] == [4]
    assert [t["id"] for t in svc.list_tasks(tag="home", status="todo")] == [2]


@pytest.mark.parametrize("kwargs", [{"status": "bogus"}, {"sort": "created"}, {"sort": ""}])
def test_fr9_invalid_filter_or_sort_is_validation_error(svc, kwargs):
    with pytest.raises(ValidationError):
        svc.list_tasks(**kwargs)


def test_fr9_empty_store_lists_empty(svc):
    assert svc.list_tasks() == []


# ------------------------------------------------------------- FR-10 persistence
def test_fr10_state_persists_across_instances(store):
    TaskService(store).add_task("a", tags=["x"])
    again = TaskService(store)
    assert again.get_task(1)["tags"] == ["x"]
    assert again.add_task("b")["id"] == 2


def test_fr10_next_id_persists_after_delete_and_restart(store):
    s = TaskService(store)
    s.add_task("a")
    s.add_task("b")
    s.delete_task(2)
    assert TaskService(store).add_task("c")["id"] == 3


def test_fr10_reading_does_not_create_file(store):
    assert TaskService(store).list_tasks() == []
    assert not store.exists()


def test_fr10_file_is_valid_json(store):
    TaskService(store).add_task("a")
    assert isinstance(json.loads(store.read_text(encoding="utf-8")), dict)


def test_fr10_no_temp_files_left_behind(svc, store):
    svc.add_task("a")
    svc.update_task(1, title="b")
    svc.delete_task(1)
    assert [p.name for p in store.parent.iterdir()] == [store.name]


def test_fr10_returned_dicts_are_copies(svc):
    t = svc.add_task("a", tags=["x"])
    t["title"] = "mutated"
    t["tags"].append("y")
    fresh = svc.get_task(1)
    assert fresh["title"] == "a"
    assert fresh["tags"] == ["x"]


def test_fr10_write_failure_raises_storage_error_and_keeps_old_data(svc, store, monkeypatch):
    svc.add_task("a")
    before = store.read_bytes()

    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(StorageError):
        svc.add_task("b")
    monkeypatch.undo()
    assert store.read_bytes() == before
    assert [p.name for p in store.parent.iterdir()] == [store.name]
    assert svc.add_task("b")["id"] == 2


# ---------------------------------------------------------------- FR-11 corruption
@pytest.mark.parametrize("content", ["", "{not json", "[]", "{}", '{"tasks": "x", "next_id": 1}'])
def test_fr11_corrupt_store_raises_storage_error_and_is_untouched(store, content):
    store.write_text(content, encoding="utf-8")
    s = TaskService(store)
    for call in (
        lambda: s.list_tasks(),
        lambda: s.add_task("a"),
        lambda: s.get_task(1),
    ):
        with pytest.raises(StorageError):
            call()
    assert store.read_text(encoding="utf-8") == content


def test_fr11_all_errors_share_base_class():
    for exc in (ValidationError, TaskNotFoundError, InvalidTransitionError, StorageError):
        assert issubclass(exc, TodoError)


# ------------------------------------------------------------------- NFR-6 security
@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
def test_nfr6_store_file_is_owner_only(svc, store):
    svc.add_task("a")
    assert (store.stat().st_mode & 0o777) == 0o600
