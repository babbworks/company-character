from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage repo scanning config and section map")
console = Console()

_REPO_CONFIG = Path(__file__).parent.parent.parent / "repo-config.yml"


def _load_repo_config() -> dict:
    with open(_REPO_CONFIG) as f:
        return yaml.safe_load(f) or {"ignore": [], "pin": []}


def _save_repo_config(data: dict):
    with open(_REPO_CONFIG, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


@app.command("list")
def list_repos():
    """Show cached scan results with ignore/pin status."""
    import json
    from cc_admin import config
    admin_cfg = config.load_admin_config()
    cache = config.dist_path(admin_cfg).parent / "dist" / "scan-cache.json"

    rc = _load_repo_config()
    ignored = set(rc.get("ignore", []))
    pinned = set(rc.get("pin", []))

    if not cache.exists():
        console.print("[dim]No scan cache. Run `cc-admin scan` first.[/dim]")
        return

    with open(cache) as f:
        repos = json.load(f)

    table = Table(show_lines=True)
    table.add_column("Repo", style="cyan")
    table.add_column("Topics")
    table.add_column("Status")
    table.add_column("Commits 7d", justify="right")

    for r in repos:
        name = r["name"]
        status = "[yellow]ignored[/yellow]" if name in ignored else ("[green]pinned[/green]" if name in pinned else "active")
        table.add_row(name, ", ".join(r.get("babb_topics", [])), status, str(r.get("signals", {}).get("commits_7d", 0)))
    console.print(table)


@app.command("ignore")
def ignore_repo(name: str = typer.Argument(..., help="Repo name to ignore")):
    """Exclude a repo from future scans."""
    rc = _load_repo_config()
    if name not in rc["ignore"]:
        rc["ignore"].append(name)
        rc["pin"] = [r for r in rc.get("pin", []) if r != name]
    _save_repo_config(rc)
    console.print(f"[green]Ignored[/green] {name}")


@app.command("pin")
def pin_repo(name: str = typer.Argument(..., help="Repo name to always include")):
    """Always include a repo even without babb-* topics."""
    rc = _load_repo_config()
    if name not in rc.get("pin", []):
        rc.setdefault("pin", []).append(name)
        rc["ignore"] = [r for r in rc.get("ignore", []) if r != name]
    _save_repo_config(rc)
    console.print(f"[green]Pinned[/green] {name}")


@app.command("unignore")
def unignore_repo(name: str = typer.Argument(...)):
    """Remove a repo from the ignore list."""
    rc = _load_repo_config()
    rc["ignore"] = [r for r in rc.get("ignore", []) if r != name]
    _save_repo_config(rc)
    console.print(f"[green]Unignored[/green] {name}")


@app.command("section-map")
def section_map(
    add: bool = typer.Option(False, "--add", help="Add a new header→slot mapping"),
    remove: str = typer.Option(None, "--remove", help="Remove a header from the map"),
):
    """View or edit the section-map.yml."""
    from cc_admin import config
    admin_cfg = config.load_admin_config()
    sm_file = config.state_path(admin_cfg) / "section-map.yml"

    with open(sm_file) as f:
        state = yaml.safe_load(f)

    section_map_data = state.get("section_map", {})

    if remove:
        if remove in section_map_data:
            del section_map_data[remove]
            state["section_map"] = section_map_data
            with open(sm_file, "w") as f:
                yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
            console.print(f"[green]Removed[/green] '{remove}' from section map")
        else:
            console.print(f"[dim]'{remove}' not found in section map[/dim]")
        return

    if add:
        from rich.prompt import Prompt
        header = Prompt.ask("[cyan]README header text[/cyan]")
        slot = Prompt.ask("[cyan]Knowledge slot name[/cyan]")
        section_map_data[header] = slot
        state["section_map"] = section_map_data
        with open(sm_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
        console.print(f"[green]Added[/green] '{header}' → {slot}")
        return

    table = Table(title="section-map.yml", show_lines=True)
    table.add_column("README Header", style="cyan")
    table.add_column("Knowledge Slot")
    for header, slot in section_map_data.items():
        table.add_row(header, slot)
    console.print(table)
