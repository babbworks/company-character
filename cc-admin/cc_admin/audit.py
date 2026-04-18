import json
from datetime import datetime, timezone
from pathlib import Path

_LOG = Path(__file__).parent.parent / "audit" / "log.json"


def _load() -> list[dict]:
    if not _LOG.exists():
        return []
    with open(_LOG) as f:
        return json.load(f)


def _save(entries: list[dict]):
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def record(operation: str, detail: dict):
    entries = _load()
    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        **detail,
    })
    _save(entries[-200:])


def all_entries() -> list[dict]:
    return _load()
