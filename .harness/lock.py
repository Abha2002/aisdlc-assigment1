"""HUMAN-ONLY: record sha256 of every file the coding agent must not change.

Run once after you have reviewed tests/, .harness/ and pyproject.toml, BEFORE
/speckit.implement. Re-run only for a legitimate, documented change (and note
it in evidence/harness-log.md). The agent must never run this script.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name("lock.json")


def locked_files():
    files = [ROOT / "pyproject.toml", ROOT / "requirements-dev.txt"]
    files += sorted((ROOT / "tests").rglob("*.py"))
    files += sorted(p for p in Path(__file__).parent.glob("*.py"))
    return [f for f in files if f.is_file()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current():
    return {str(f.relative_to(ROOT)).replace("\\", "/"): digest(f) for f in locked_files()}


if __name__ == "__main__":
    LOCK.write_text(json.dumps(current(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"locked {len(current())} files -> {LOCK}")
