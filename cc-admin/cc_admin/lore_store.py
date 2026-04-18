import json
import uuid
from datetime import date
from pathlib import Path

_STORE = Path(__file__).parent.parent / "lore" / "entries.json"


def _load() -> list[dict]:
    with open(_STORE) as f:
        return json.load(f)


def _save(entries: list[dict]):
    with open(_STORE, "w") as f:
        json.dump(entries, f, indent=2)


def all_entries() -> list[dict]:
    return _load()


def get(entry_id: str) -> dict | None:
    return next((e for e in _load() if e["id"] == entry_id), None)


def add(title: str, content: str, category: str, tags: list[str]) -> dict:
    entry = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
        "created": str(date.today()),
        "updated": str(date.today()),
    }
    entries = _load()
    entries.append(entry)
    _save(entries)
    return entry


def update(entry_id: str, **fields) -> dict | None:
    entries = _load()
    for entry in entries:
        if entry["id"] == entry_id:
            entry.update(fields)
            entry["updated"] = str(date.today())
            _save(entries)
            return entry
    return None


def delete(entry_id: str) -> bool:
    entries = _load()
    filtered = [e for e in entries if e["id"] != entry_id]
    if len(filtered) == len(entries):
        return False
    _save(filtered)
    return True
