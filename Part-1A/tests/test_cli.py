"""CLI contract tests derived from spec requirement FR-12."""
import json
import os
import subprocess
import sys
from pathlib import Path

from todo.cli import main


def run(args, store, capsys):
    rc = main(["--file", str(store), *args])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_fr12_add_prints_task_json(store, capsys):
    rc, out, err = run(
        ["add", "Buy milk", "--priority", "high", "--tag", "Home", "--tag", "errands"],
        store,
        capsys,
    )
    assert (rc, err) == (0, "")
    t = json.loads(out)
    assert (t["id"], t["priority"], t["tags"], t["status"]) == (
        1,
        "high",
        ["home", "errands"],
        "todo",
    )


def test_fr12_get_list_status_edit_delete_flow(store, capsys):
    run(["add", "a", "--priority", "low", "--tag", "x"], store, capsys)
    run(["add", "b", "--priority", "high", "--tag", "y"], store, capsys)

    rc, out, _ = run(["list"], store, capsys)
    assert rc == 0
    assert [t["id"] for t in json.loads(out)] == [2, 1]

    rc, out, _ = run(["list", "--tag", "X"], store, capsys)
    assert [t["id"] for t in json.loads(out)] == [1]

    rc, out, _ = run(["status", "1", "in_progress"], store, capsys)
    assert rc == 0
    assert json.loads(out)["status"] == "in_progress"

    rc, out, _ = run(["list", "--status", "in_progress"], store, capsys)
    assert [t["id"] for t in json.loads(out)] == [1]

    rc, out, _ = run(
        ["edit", "1", "--title", "A2", "--priority", "medium", "--tag", "z"], store, capsys
    )
    t = json.loads(out)
    assert rc == 0
    assert (t["title"], t["priority"], t["tags"]) == ("A2", "medium", ["z"])

    rc, out, _ = run(["get", "1"], store, capsys)
    assert rc == 0
    assert json.loads(out)["title"] == "A2"

    rc, out, _ = run(["delete", "1"], store, capsys)
    assert rc == 0
    assert json.loads(out) == {"deleted": 1}

    rc, out, _ = run(["list", "--sort", "id"], store, capsys)
    assert [t["id"] for t in json.loads(out)] == [2]


def test_fr12_empty_list_is_empty_json_array(store, capsys):
    rc, out, _ = run(["list"], store, capsys)
    assert rc == 0
    assert json.loads(out) == []


def test_fr12_domain_errors_exit_2_with_message_on_stderr_only(store, capsys):
    for args in (["get", "9"], ["add", ""], ["add", "a", "--priority", "urgent"]):
        rc, out, err = run(args, store, capsys)
        assert rc == 2
        assert out == ""
        assert err.startswith("error: ")


def test_fr12_invalid_transition_exit_2(store, capsys):
    run(["add", "a"], store, capsys)
    rc, out, err = run(["status", "1", "todo"], store, capsys)
    assert (rc, out) == (2, "")
    assert err.startswith("error: ")


def test_fr12_corrupt_store_exit_2(store, capsys):
    store.write_text("{oops", encoding="utf-8")
    rc, out, err = run(["list"], store, capsys)
    assert (rc, out) == (2, "")
    assert err.startswith("error: ")


def test_fr12_module_entrypoint(store):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "todo", "--file", str(store), "list"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert p.returncode == 0
    assert json.loads(p.stdout) == []
