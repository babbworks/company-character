import base64
import os
from datetime import datetime, timedelta, timezone

import requests


_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url: str, params: dict | None = None) -> dict | list:
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _paginate(url: str, params: dict | None = None) -> list:
    params = {**(params or {}), "per_page": 100}
    results = []
    while url:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)
        resp.raise_for_status()
        results.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
        params = None
    return results


def list_repos(org: str) -> list[dict]:
    return _paginate(f"{_BASE}/orgs/{org}/repos", {"type": "public"})


def get_readme(org: str, repo: str) -> str | None:
    try:
        data = _get(f"{_BASE}/repos/{org}/{repo}/readme")
        return base64.b64decode(data["content"]).decode("utf-8")
    except requests.HTTPError:
        return None


def get_signals(org: str, repo: str) -> dict:
    signals = {}

    try:
        commits = _get(f"{_BASE}/repos/{org}/{repo}/commits", {"per_page": 1})
        if commits:
            signals["last_commit"] = commits[0]["commit"]["committer"]["date"][:10]
    except requests.HTTPError:
        pass

    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent = _paginate(f"{_BASE}/repos/{org}/{repo}/commits", {"since": since})
        signals["commits_7d"] = len(recent)
    except requests.HTTPError:
        signals["commits_7d"] = 0

    try:
        prs = _get(f"{_BASE}/repos/{org}/{repo}/pulls", {"state": "open", "per_page": 100})
        signals["open_prs"] = len(prs)
        signals["open_pr_titles"] = [pr["title"] for pr in prs[:5]]
    except requests.HTTPError:
        signals["open_prs"] = 0

    try:
        releases = _get(f"{_BASE}/repos/{org}/{repo}/releases", {"per_page": 3})
        signals["recent_releases"] = [r["tag_name"] for r in releases]
    except requests.HTTPError:
        signals["recent_releases"] = []

    return signals
