import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from cc_admin import announce_store, audit, config, lore_store, qa_store

_ALIAS_STORE = Path(__file__).parent.parent / "aliases" / "aliases.json"
_EGG_STORE = Path(__file__).parent.parent / "persona" / "easter-eggs.json"


def _load_aliases() -> dict:
    if _ALIAS_STORE.exists():
        with open(_ALIAS_STORE) as f:
            return json.load(f)
    return {}


def _load_eggs() -> list[dict]:
    if _EGG_STORE.exists():
        with open(_EGG_STORE) as f:
            return json.load(f)
    return []


def load_overrides(repo_id: str) -> dict:
    override_file = config.overrides_path() / f"{repo_id}.yml"
    if override_file.exists():
        with open(override_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def apply_overrides(record: dict, overrides: dict) -> tuple[dict, dict]:
    applied = {}
    if not overrides:
        return record, applied

    now_iso = datetime.now(timezone.utc).isoformat()
    slots = record["knowledge"]

    for slot, directive in overrides.get("slots", {}).items():
        if isinstance(directive, str):
            slots[slot] = directive
            applied[slot] = "replace"
        elif isinstance(directive, dict):
            action = directive.get("action")
            if action == "suppress":
                slots.pop(slot, None)
                applied[slot] = "suppress"
            elif action == "embargo":
                until = directive.get("until", "")
                if now_iso < until:
                    slots.pop(slot, None)
                    applied[slot] = f"embargo until {until}"
                elif "value" in directive:
                    slots[slot] = directive["value"]
                    applied[slot] = "embargo-lifted"
            elif action == "replace" and "value" in directive:
                slots[slot] = directive["value"]
                applied[slot] = "replace"
            elif action == "confidence":
                record.setdefault("slot_meta", {})[slot] = {"confidence": directive.get("level", "speculative")}
                applied[slot] = f"confidence:{directive.get('level', 'speculative')}"

    for key in ("tone", "aliases", "featured_order", "strategic_framing", "response_length", "cross_refs"):
        if key in overrides:
            record[key] = overrides[key]

    return record, applied


def build_knowledge(scan_results: list[dict], admin_config: dict) -> dict:
    state = config.state_path(admin_config)

    now_md = ""
    now_file = state / "NOW.md"
    if now_file.exists():
        now_md = now_file.read_text().strip()

    roadmap_md = ""
    roadmap_file = state / "roadmap.md"
    if roadmap_file.exists():
        roadmap_md = roadmap_file.read_text().strip()

    aliases = _load_aliases()
    tools = []
    audit_detail = {"repos": [], "overrides_applied": {}}

    for repo in scan_results:
        record = {
            "id": repo["name"],
            "repo": f"{admin_config['org']}/{repo['name']}",
            "topics": repo["babb_topics"],
            "category": repo["category"],
            "knowledge": repo["slots"],
            "signals": repo["signals"],
        }
        overrides = load_overrides(repo["name"])
        record, applied = apply_overrides(record, overrides)

        alias_entry = aliases.get(repo["name"], {})
        if alias_entry.get("aliases"):
            record.setdefault("aliases", []).extend(alias_entry["aliases"])
        if alias_entry.get("xrefs"):
            record["xrefs"] = alias_entry["xrefs"]

        tools.append(record)
        slots_sourced = {k: ("override" if k in applied else "readme") for k in repo["slots"]}
        audit_detail["repos"].append(repo["name"])
        if applied:
            audit_detail["overrides_applied"][repo["name"]] = applied
        audit_detail[repo["name"]] = {"slots_sourced": slots_sourced}

    tools.sort(key=lambda r: r.get("featured_order", 999))

    qa_pairs = [p for p in qa_store.all_pairs() if p.get("mode") in ("offline", "both", None, "")]
    lore = lore_store.all_entries()
    announcement = announce_store.active()
    easter_eggs = _load_eggs()

    audit.record("build", audit_detail)

    return {
        "org": admin_config["org"],
        "brand": admin_config.get("brand", admin_config["org"]),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "now": now_md,
        "roadmap": roadmap_md,
        "tools": tools,
        "qa": qa_pairs,
        "lore": lore,
        "easter_eggs": easter_eggs,
        "announcement": announcement["message"] if announcement else None,
    }


def write_dist(knowledge: dict, admin_config: dict) -> Path:
    out = config.dist_path(admin_config)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "knowledge.json"
    with open(dest, "w") as f:
        json.dump(knowledge, f, indent=2)
    return dest
