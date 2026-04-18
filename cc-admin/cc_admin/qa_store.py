import json
import re
import uuid
from datetime import date
from pathlib import Path

_STORE = Path(__file__).parent.parent / "qa" / "pairs.json"


def _load() -> list[dict]:
    with open(_STORE) as f:
        return json.load(f)


def _save(pairs: list[dict]):
    with open(_STORE, "w") as f:
        json.dump(pairs, f, indent=2)


def all_pairs() -> list[dict]:
    return _load()


def get(pair_id: str) -> dict | None:
    return next((p for p in _load() if p["id"] == pair_id), None)


def add(question: str, answer: str, variants: list[str], category: str, tags: list[str], mode: str, author: str) -> dict:
    pair = {
        "id": uuid.uuid4().hex[:8],
        "question": question,
        "variants": variants,
        "answer": answer,
        "category": category,
        "tags": tags,
        "mode": mode,
        "author": author,
        "created": str(date.today()),
        "updated": str(date.today()),
    }
    pairs = _load()
    pairs.append(pair)
    _save(pairs)
    return pair


def update(pair_id: str, **fields) -> dict | None:
    pairs = _load()
    for pair in pairs:
        if pair["id"] == pair_id:
            pair.update(fields)
            pair["updated"] = str(date.today())
            _save(pairs)
            return pair
    return None


def delete(pair_id: str) -> bool:
    pairs = _load()
    filtered = [p for p in pairs if p["id"] != pair_id]
    if len(filtered) == len(pairs):
        return False
    _save(filtered)
    return True


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())


def match(query: str, pairs: list[dict] | None = None) -> dict | None:
    if pairs is None:
        pairs = _load()
    q = _normalize(query)
    q_words = set(q.split())

    best, best_score = None, 0.0
    for pair in pairs:
        candidates = [pair["question"]] + pair.get("variants", [])
        for candidate in candidates:
            c_words = set(_normalize(candidate).split())
            if not c_words:
                continue
            overlap = len(q_words & c_words) / len(c_words)
            if overlap > best_score:
                best_score = overlap
                best = pair

    return best if best_score >= 0.5 else None
