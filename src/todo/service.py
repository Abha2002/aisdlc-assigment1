"""Task service and persisted store implementation."""

import copy
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from todo.errors import (
    InvalidTransitionError,
    StorageError,
    TaskNotFoundError,
    ValidationError,
)

_TAG_PATTERN = re.compile(r"^[a-z0-9-]{1,20}$")
_PRIORITIES = {"low", "medium", "high"}
_STATUSES = {"todo", "in_progress", "done"}
_TRANSITIONS = {
    ("todo", "in_progress"),
    ("todo", "done"),
    ("in_progress", "todo"),
    ("in_progress", "done"),
    ("done", "todo"),
}
_TASK_KEYS = {"id", "title", "priority", "status", "tags", "created_at"}


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_id(task_id):
    if not _is_int(task_id):
        raise ValidationError("task id must be an integer")
    return task_id


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError("title must be a string")
    stripped = title.strip()
    if not 1 <= len(stripped) <= 100:
        raise ValidationError("title must contain 1 through 100 characters")
    return stripped


def validate_priority(priority):
    if not isinstance(priority, str) or priority not in _PRIORITIES:
        raise ValidationError("priority must be low, medium, or high")
    return priority


def normalize_tags(tags):
    if not isinstance(tags, list):
        raise ValidationError("tags must be a list of strings")
    result = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValidationError("tags must be a list of strings")
        normalized = tag.strip().lower()
        if not _TAG_PATTERN.fullmatch(normalized):
            raise ValidationError("invalid tag")
        if normalized not in result:
            result.append(normalized)
            if len(result) > 10:
                raise ValidationError("no more than 10 distinct tags are allowed")
    return result


def validate_status(status):
    if not isinstance(status, str) or status not in _STATUSES:
        raise ValidationError("invalid status")
    return status


def validate_sort(sort):
    if sort not in {"priority", "id"}:
        raise ValidationError("sort must be priority or id")
    return sort


def _valid_created_at(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _validate_task(task, seen_ids):
    if not isinstance(task, dict) or set(task) != _TASK_KEYS:
        raise StorageError("invalid task in store")
    task_id = task["id"]
    if not _is_int(task_id) or task_id < 1 or task_id in seen_ids:
        raise StorageError("invalid task id in store")
    title = task["title"]
    if not isinstance(title, str) or title != title.strip():
        raise StorageError("invalid task title in store")
    if not 1 <= len(title) <= 100:
        raise StorageError("invalid task title in store")
    if task["priority"] not in _PRIORITIES:
        raise StorageError("invalid task priority in store")
    if task["status"] not in _STATUSES:
        raise StorageError("invalid task status in store")
    if not isinstance(task["tags"], list):
        raise StorageError("invalid task tags in store")
    try:
        normalized = normalize_tags(task["tags"])
    except ValidationError as exc:
        raise StorageError("invalid task tags in store") from exc
    if normalized != task["tags"]:
        raise StorageError("invalid task tags in store")
    if not _valid_created_at(task["created_at"]):
        raise StorageError("invalid task timestamp in store")
    seen_ids.add(task_id)


def validate_store(store):
    if not isinstance(store, dict) or set(store) != {"version", "next_id", "tasks"}:
        raise StorageError("invalid store shape")
    if not _is_int(store["version"]) or store["version"] != 1:
        raise StorageError("unsupported store version")
    next_id = store["next_id"]
    if not _is_int(next_id) or next_id < 1:
        raise StorageError("invalid next_id")
    tasks = store["tasks"]
    if not isinstance(tasks, list):
        raise StorageError("invalid tasks list")
    seen_ids = set()
    for task in tasks:
        _validate_task(task, seen_ids)
    if tasks and next_id <= max(task["id"] for task in tasks):
        raise StorageError("invalid next_id")
    return store


def task_copy(task):
    return copy.deepcopy(task)


class TaskService:
    def __init__(self, path):
        self.path = Path(path)

    def _reload(self):
        if not self.path.exists():
            return {"version": 1, "next_id": 1, "tasks": []}
        try:
            content = self.path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise StorageError("could not read store") from exc
        if content == "":
            raise StorageError("store is empty")
        try:
            store = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise StorageError("invalid JSON in store") from exc
        return validate_store(store)

    def _save(self, store):
        validate_store(store)
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(
                dir=str(self.path.parent), prefix=f".{self.path.name}.", suffix=".tmp"
            )
            if os.name == "posix":
                os.chmod(temp_path, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(store, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            temp_path = None
        except (OSError, TypeError, ValueError) as exc:
            raise StorageError("could not save store") from exc
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass

    @staticmethod
    def _find(store, task_id):
        validate_id(task_id)
        for task in store["tasks"]:
            if task["id"] == task_id:
                return task
        raise TaskNotFoundError("task not found")

    def add_task(self, title, priority="medium", tags=None):
        store = self._reload()
        clean_title = validate_title(title)
        clean_priority = validate_priority(priority)
        clean_tags = [] if tags is None else normalize_tags(tags)
        task_id = store["next_id"]
        task = {
            "id": task_id,
            "title": clean_title,
            "priority": clean_priority,
            "status": "todo",
            "tags": clean_tags,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        new_store = copy.deepcopy(store)
        new_store["tasks"].append(task)
        new_store["next_id"] = task_id + 1
        self._save(new_store)
        return task_copy(task)

    def get_task(self, task_id):
        store = self._reload()
        task = self._find(store, task_id)
        return task_copy(task)

    def update_task(self, task_id, title=None, priority=None, tags=None):
        store = self._reload()
        task = self._find(store, task_id)
        if title is None and priority is None and tags is None:
            raise ValidationError("at least one field must be provided")
        clean_title = validate_title(title) if title is not None else None
        clean_priority = validate_priority(priority) if priority is not None else None
        clean_tags = normalize_tags(tags) if tags is not None else None
        updated = task_copy(task)
        if clean_title is not None:
            updated["title"] = clean_title
        if clean_priority is not None:
            updated["priority"] = clean_priority
        if clean_tags is not None:
            updated["tags"] = clean_tags
        new_store = copy.deepcopy(store)
        for index, current in enumerate(new_store["tasks"]):
            if current["id"] == task_id:
                new_store["tasks"][index] = updated
                break
        self._save(new_store)
        return task_copy(updated)

    def delete_task(self, task_id):
        store = self._reload()
        task = self._find(store, task_id)
        new_store = copy.deepcopy(store)
        new_store["tasks"] = [item for item in new_store["tasks"] if item["id"] != task["id"]]
        self._save(new_store)
        return None

    def set_status(self, task_id, new_status):
        store = self._reload()
        task = self._find(store, task_id)
        clean_status = validate_status(new_status)
        transition = (task["status"], clean_status)
        if transition not in _TRANSITIONS:
            raise InvalidTransitionError("invalid status transition")
        updated = task_copy(task)
        updated["status"] = clean_status
        new_store = copy.deepcopy(store)
        for index, current in enumerate(new_store["tasks"]):
            if current["id"] == task_id:
                new_store["tasks"][index] = updated
                break
        self._save(new_store)
        return task_copy(updated)

    def list_tasks(self, tag=None, status=None, sort="priority"):
        store = self._reload()
        clean_sort = validate_sort(sort)
        clean_status = validate_status(status) if status is not None else None
        clean_tag = None
        if tag is not None:
            if not isinstance(tag, str):
                raise ValidationError("tag must be a string")
            clean_tag = tag.strip().lower()
            if not _TAG_PATTERN.fullmatch(clean_tag):
                raise ValidationError("invalid tag")
        tasks = []
        for task in store["tasks"]:
            if clean_status is not None and task["status"] != clean_status:
                continue
            if clean_tag is not None and clean_tag not in task["tags"]:
                continue
            tasks.append(task_copy(task))
        if clean_sort == "id":
            return sorted(tasks, key=lambda item: item["id"])
        rank = {"high": 0, "medium": 1, "low": 2}
        return sorted(tasks, key=lambda item: (rank[item["priority"]], item["id"]))
