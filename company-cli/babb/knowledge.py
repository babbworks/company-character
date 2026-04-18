import json
from pathlib import Path

_DIST = Path(__file__).parent.parent / "dist" / "knowledge.json"


def load() -> dict:
    if not _DIST.exists():
        return {"tools": [], "now": "", "org": "babbworks", "built_at": None, "qa": [], "lore": [], "announcement": None}
    with open(_DIST) as f:
        return json.load(f)


def get_tool(knowledge: dict, name: str) -> dict | None:
    name = name.lower()
    for tool in knowledge["tools"]:
        if tool["id"].lower() == name:
            return tool
        if name in [a.lower() for a in tool.get("aliases", [])]:
            return tool
    return None


def active_tools(knowledge: dict) -> list[dict]:
    return sorted(
        knowledge["tools"],
        key=lambda t: t.get("signals", {}).get("commits_7d", 0),
        reverse=True,
    )


def recent_releases(knowledge: dict) -> list[tuple[str, str]]:
    out = []
    for tool in knowledge["tools"]:
        for release in tool.get("signals", {}).get("recent_releases", []):
            out.append((tool["id"], release))
    return out
