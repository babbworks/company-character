import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage tool aliases and cross-references")
console = Console()

_STORE = Path(__file__).parent.parent.parent / "aliases" / "aliases.json"


def _load() -> dict:
    with open(_STORE) as f:
        return json.load(f)


def _save(data: dict):
    with open(_STORE, "w") as f:
        json.dump(data, f, indent=2)


@app.command("list")
def list_aliases(tool: str = typer.Option(None, "--tool", "-t")):
    """List all aliases and cross-references."""
    data = _load()
    items = {tool: data[tool]} if tool and tool in data else data

    if not items:
        console.print("[dim]No aliases set.[/dim]")
        return

    for repo, entry in items.items():
        console.print(f"\n[bold cyan]{repo}[/bold cyan]")
        aliases = entry.get("aliases", [])
        xrefs = entry.get("xrefs", [])
        if aliases:
            console.print(f"  [dim]aliases:[/dim] {', '.join(aliases)}")
        if xrefs:
            for x in xrefs:
                console.print(f"  [dim]→[/dim] {x['tool']}  [dim]{x.get('note', '')}[/dim]")
        if not aliases and not xrefs:
            console.print("  [dim]empty[/dim]")


@app.command("add")
def add_alias(
    tool: str = typer.Argument(..., help="Tool ID e.g. bitpads"),
    alias: str = typer.Argument(..., help="Alternate name e.g. 'bp'"),
):
    """Add an alias for a tool."""
    data = _load()
    data.setdefault(tool, {"aliases": [], "xrefs": []})
    if alias not in data[tool]["aliases"]:
        data[tool]["aliases"].append(alias)
    _save(data)
    console.print(f"[green]Added[/green] '{alias}' → {tool}")


@app.command("remove")
def remove_alias(
    tool: str = typer.Argument(...),
    alias: str = typer.Argument(...),
):
    """Remove an alias from a tool."""
    data = _load()
    if tool not in data or alias not in data[tool].get("aliases", []):
        console.print(f"[dim]Alias '{alias}' not found for {tool}[/dim]")
        return
    data[tool]["aliases"].remove(alias)
    _save(data)
    console.print(f"[green]Removed[/green] '{alias}' from {tool}")


@app.command("xref")
def add_xref(
    tool_a: str = typer.Argument(..., help="Source tool"),
    tool_b: str = typer.Argument(..., help="Related tool"),
    note: str = typer.Option("", "--note", "-n", help="Relationship note"),
):
    """Declare a relationship between two tools."""
    data = _load()
    data.setdefault(tool_a, {"aliases": [], "xrefs": []})
    existing = [x["tool"] for x in data[tool_a].get("xrefs", [])]
    if tool_b not in existing:
        data[tool_a].setdefault("xrefs", []).append({"tool": tool_b, "note": note})
    _save(data)
    console.print(f"[green]Cross-reference set[/green] {tool_a} → {tool_b}")
