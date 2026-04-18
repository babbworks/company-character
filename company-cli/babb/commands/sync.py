import base64
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Refresh cached GitHub signals")
console = Console()

_DIST = Path(__file__).parent.parent.parent / "dist" / "knowledge.json"
_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _fetch_signals(org: str, repo: str) -> dict:
    try:
        import requests
    except ImportError:
        return {}

    signals = {}
    try:
        commits = requests.get(f"{_BASE}/repos/{org}/{repo}/commits", headers=_headers(), params={"per_page": 1}, timeout=10).json()
        if isinstance(commits, list) and commits:
            signals["last_commit"] = commits[0]["commit"]["committer"]["date"][:10]
    except Exception:
        pass

    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent = requests.get(f"{_BASE}/repos/{org}/{repo}/commits", headers=_headers(), params={"since": since, "per_page": 100}, timeout=10).json()
        signals["commits_7d"] = len(recent) if isinstance(recent, list) else 0
    except Exception:
        signals["commits_7d"] = 0

    try:
        prs = requests.get(f"{_BASE}/repos/{org}/{repo}/pulls", headers=_headers(), params={"state": "open", "per_page": 100}, timeout=10).json()
        if isinstance(prs, list):
            signals["open_prs"] = len(prs)
            signals["open_pr_titles"] = [pr["title"] for pr in prs[:5]]
    except Exception:
        pass

    try:
        releases = requests.get(f"{_BASE}/repos/{org}/{repo}/releases", headers=_headers(), params={"per_page": 3}, timeout=10).json()
        if isinstance(releases, list):
            signals["recent_releases"] = [r["tag_name"] for r in releases]
    except Exception:
        pass

    return signals


@app.callback(invoke_without_command=True)
def sync(ctx: typer.Context):
    """Pull fresh GitHub signals for all indexed tools."""
    if ctx.invoked_subcommand:
        return

    if not _DIST.exists():
        console.print("[yellow]No knowledge base found. Nothing to sync.[/yellow]")
        raise typer.Exit(1)

    try:
        import requests
    except ImportError:
        console.print("[red]requests package not installed. Run: pip install requests[/red]")
        raise typer.Exit(1)

    with open(_DIST) as f:
        knowledge = json.load(f)

    org = knowledge.get("org", "babbworks")
    tools = knowledge.get("tools", [])

    if not tools:
        console.print("[dim]No tools indexed.[/dim]")
        return

    updated = 0
    with console.status(f"Syncing signals from {org}..."):
        for tool in tools:
            repo_name = tool["repo"].split("/")[-1]
            fresh = _fetch_signals(org, repo_name)
            if fresh:
                tool["signals"].update(fresh)
                updated += 1

    knowledge["synced_at"] = datetime.now(timezone.utc).isoformat()

    with open(_DIST, "w") as f:
        json.dump(knowledge, f, indent=2)

    console.print(f"[green]Synced[/green] {updated} tool(s).")
    for tool in tools:
        s = tool.get("signals", {})
        console.print(f"  [cyan]{tool['id']}[/cyan] — {s.get('commits_7d', 0)} commits this week, {s.get('open_prs', 0)} open PRs")
