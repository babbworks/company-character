import json
import uuid
from datetime import date
from pathlib import Path

_STORE = Path(__file__).parent.parent / "announce" / "announcements.json"


def _load() -> list[dict]:
    with open(_STORE) as f:
        return json.load(f)


def _save(items: list[dict]):
    with open(_STORE, "w") as f:
        json.dump(items, f, indent=2)


def all_announcements() -> list[dict]:
    return _load()


def active() -> dict | None:
    today = str(date.today())
    for item in _load():
        if not item.get("active"):
            continue
        expires = item.get("expires")
        if expires and today > expires:
            continue
        return item
    return None


def set_announcement(message: str, expires: str | None = None) -> dict:
    items = _load()
    for item in items:
        item["active"] = False
    new = {
        "id": uuid.uuid4().hex[:8],
        "message": message,
        "active": True,
        "expires": expires,
        "created": str(date.today()),
    }
    items.append(new)
    _save(items)
    return new


def clear() -> int:
    items = _load()
    count = sum(1 for i in items if i.get("active"))
    for item in items:
        item["active"] = False
    _save(items)
    return count


def expire_old() -> int:
    today = str(date.today())
    items = _load()
    count = 0
    for item in items:
        if item.get("active") and item.get("expires") and today > item["expires"]:
            item["active"] = False
            count += 1
    _save(items)
    return count
