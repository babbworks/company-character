import json
import os
import uuid
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

app = typer.Typer(help="Manage Babb's personality and easter eggs")
console = Console()

_EGGS = Path(__file__).parent.parent.parent / "persona" / "easter-eggs.json"


def _load_eggs() -> list[dict]:
    with open(_EGGS) as f:
        return json.load(f)


def _save_eggs(eggs: list[dict]):
    with open(_EGGS, "w") as f:
        json.dump(eggs, f, indent=2)


def _personality_file(admin_config: dict) -> Path:
    from cc_admin import config
    return config.state_path(admin_config) / "personality.md"


@app.command("show")
def show_persona():
    """Display the current personality definition."""
    from cc_admin import config
    admin_cfg = config.load_admin_config()
    pfile = _personality_file(admin_cfg)
    if not pfile.exists():
        console.print("[yellow]No personality.md found in babb-state.[/yellow]")
        return
    console.print(Panel(pfile.read_text(), title="[bold cyan]Babb — Personality[/bold cyan]", border_style="cyan", padding=(1, 2)))


@app.command("edit")
def edit_persona():
    """Open personality.md in $EDITOR."""
    from cc_admin import config
    admin_cfg = config.load_admin_config()
    pfile = _personality_file(admin_cfg)
    editor = os.environ.get("EDITOR", "nano")
    os.system(f'{editor} "{pfile}"')


@app.command("easter-egg")
def easter_egg(ctx: typer.Context):
    """Manage easter eggs — use subcommands: list, add, delete, test."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


_egg_app = typer.Typer()
app.add_typer(_egg_app, name="easter-egg")


@_egg_app.command("list")
def list_eggs():
    """List all easter eggs."""
    eggs = _load_eggs()
    if not eggs:
        console.print("[dim]No easter eggs set.[/dim]")
        return
    table = Table(show_lines=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Trigger", style="cyan")
    table.add_column("Response", max_width=60)
    for egg in eggs:
        table.add_row(egg["id"], egg["trigger"], egg["response"][:80] + ("…" if len(egg["response"]) > 80 else ""))
    console.print(table)


@_egg_app.command("add")
def add_egg():
    """Add an easter egg."""
    trigger = Prompt.ask("[cyan]Trigger phrase[/cyan]")
    response = Prompt.ask("[cyan]Response[/cyan]")
    eggs = _load_eggs()
    egg = {"id": uuid.uuid4().hex[:8], "trigger": trigger, "response": response, "created": str(date.today())}
    eggs.append(egg)
    _save_eggs(eggs)
    console.print(f"[green]Added[/green] [{egg['id']}] '{trigger}'")


@_egg_app.command("delete")
def delete_egg(egg_id: str = typer.Argument(...)):
    """Delete an easter egg by ID."""
    eggs = _load_eggs()
    filtered = [e for e in eggs if e["id"] != egg_id]
    if len(filtered) == len(eggs):
        console.print(f"[red]No easter egg with ID '{egg_id}'[/red]")
        return
    _save_eggs(filtered)
    console.print("[green]Deleted.[/green]")


@_egg_app.command("test")
def test_egg(query: str = typer.Argument(...)):
    """Test whether a query triggers an easter egg."""
    import re
    eggs = _load_eggs()
    q = re.sub(r"[^\w\s]", "", query.lower())
    for egg in eggs:
        t = re.sub(r"[^\w\s]", "", egg["trigger"].lower())
        if t in q or all(w in q.split() for w in t.split()):
            console.print(f"\n[green]Triggered[/green] [{egg['id']}]")
            console.print(f"[bold]Response:[/bold] {egg['response']}")
            return
    console.print("[dim]No easter egg triggered.[/dim]")
