from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from cc_admin import config

app = typer.Typer(help="Manage per-repo slot overrides")
console = Console()


def _override_file(repo: str) -> Path:
    return config.overrides_path() / f"{repo}.yml"


def _load_repo(repo: str) -> dict:
    f = _override_file(repo)
    if not f.exists():
        return {}
    with open(f) as fh:
        return yaml.safe_load(fh) or {}


def _save_repo(repo: str, data: dict):
    f = _override_file(repo)
    with open(f, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False, allow_unicode=True)


@app.command("list")
def list_overrides(repo: str = typer.Option(None, "--repo", "-r", help="Filter by repo")):
    """List all active overrides."""
    override_dir = config.overrides_path()
    files = [override_dir / f"{repo}.yml"] if repo else sorted(override_dir.glob("*.yml"))

    if not files:
        console.print("[dim]No overrides set.[/dim]")
        return

    for f in files:
        if not f.exists():
            continue
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        if not data:
            continue

        console.print(f"\n[bold cyan]{f.stem}[/bold cyan]")
        slots = data.get("slots", {})
        for slot, directive in slots.items():
            if isinstance(directive, str):
                console.print(f"  [yellow]{slot}[/yellow] → replace: {str(directive)[:80]}")
            elif isinstance(directive, dict):
                action = directive.get("action", "?")
                detail = directive.get("until") or directive.get("value", "")
                console.print(f"  [yellow]{slot}[/yellow] → {action}: {str(detail)[:80]}")
        for key in ("tone", "aliases", "response_length", "strategic_framing"):
            if key in data:
                console.print(f"  [dim]{key}:[/dim] {data[key]}")


@app.command("set")
def set_override(
    repo: str = typer.Argument(...),
    slot: str = typer.Argument(...),
    value: str = typer.Argument(...),
):
    """Replace a slot value for a repo."""
    data = _load_repo(repo)
    data.setdefault("slots", {})[slot] = {"action": "replace", "value": value}
    _save_repo(repo, data)
    console.print(f"[green]Set[/green] {repo}/{slot}")


@app.command("suppress")
def suppress_override(
    repo: str = typer.Argument(...),
    slot: str = typer.Argument(...),
):
    """Suppress a slot — hide it from dist/ entirely."""
    data = _load_repo(repo)
    data.setdefault("slots", {})[slot] = {"action": "suppress"}
    _save_repo(repo, data)
    console.print(f"[green]Suppressed[/green] {repo}/{slot}")


@app.command("embargo")
def embargo_override(
    repo: str = typer.Argument(...),
    slot: str = typer.Argument(...),
    until: str = typer.Option(..., "--until", help="ISO date e.g. 2026-06-01"),
    value: str = typer.Option(None, "--value", help="Value to reveal after embargo lifts"),
):
    """Hide a slot until a date."""
    data = _load_repo(repo)
    directive = {"action": "embargo", "until": until}
    if value:
        directive["value"] = value
    data.setdefault("slots", {})[slot] = directive
    _save_repo(repo, data)
    console.print(f"[green]Embargoed[/green] {repo}/{slot} until {until}")


@app.command("tone")
def set_tone(
    repo: str = typer.Argument(...),
    tone: str = typer.Argument(..., help="technical | accessible | excited"),
):
    """Set tone override for a repo."""
    data = _load_repo(repo)
    data["tone"] = tone
    _save_repo(repo, data)
    console.print(f"[green]Tone set[/green] {repo} → {tone}")


@app.command("clear")
def clear_override(
    repo: str = typer.Argument(...),
    slot: str = typer.Argument(None, help="Slot to clear — omit to clear all overrides for repo"),
):
    """Remove an override."""
    data = _load_repo(repo)
    if slot:
        removed = data.get("slots", {}).pop(slot, None)
        if removed is None:
            console.print(f"[dim]No override for {repo}/{slot}[/dim]")
            return
    else:
        data = {}
    _save_repo(repo, data)
    console.print(f"[green]Cleared[/green] {repo}{f'/{slot}' if slot else ' (all)'}")
