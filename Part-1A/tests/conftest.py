"""Shared fixtures. Locked by the harness integrity gate."""
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def store(tmp_path):
    return tmp_path / "tasks.json"


@pytest.fixture
def svc(store):
    from todo.service import TaskService

    return TaskService(store)
