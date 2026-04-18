import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from cc_admin import lore_store

app = typer.Typer(help="Manage injected company lore")
console = Console()


@app.command("list")
def list_entries(
    category: str = typer.Option(None, "--category", "-c"),
    tag: str = typer.Option(None, "--tag", "-t"),
):
    """List all lore entries."""
    entries = lore_store.all_entries()
    if category:
        entries = [e for e in entries if e.get("category") == category]
    if tag:
        entries = [e for e in entries if tag in e.get("tags", [])]

    if not entries:
        console.print("[dim]No lore entries found.[/dim]")
        return

    table = Table(show_lines=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", style="cyan")
    table.add_column("Category")
    table.add_column("Content", max_width=60)

    for e in entries:
        table.add_row(
            e["id"],
            e["title"],
            e.get("category", ""),
            e["content"][:100] + ("…" if len(e["content"]) > 100 else ""),
        )
    console.print(table)


@app.command("add")
def add_entry():
    """Interactively add a lore entry."""
    console.print("\n[bold]New lore entry[/bold]\n")

    title = Prompt.ask("[cyan]Title[/cyan]")
    console.print("[dim]Content (end with a blank line):[/dim]")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    content = "\n".join(lines)

    category = Prompt.ask(
        "[cyan]Category[/cyan]",
        choices=["history", "mission", "culture", "people", "vision", "other"],
        default="other",
    )
    tags_raw = Prompt.ask("[cyan]Tags[/cyan] [dim](comma-separated or blank)[/dim]", default="")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    entry = lore_store.add(title, content, category, tags)
    console.print(f"\n[green]Added[/green] [{entry['id']}] {entry['title']}")


@app.command("edit")
def edit_entry(entry_id: str = typer.Argument(...)):
    """Edit a lore entry."""
    entry = lore_store.get(entry_id)
    if not entry:
        console.print(f"[red]No entry with ID '{entry_id}'[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Editing [{entry_id}][/bold] — leave blank to keep current\n")

    title = Prompt.ask("[cyan]Title[/cyan]", default=entry["title"])
    category = Prompt.ask("[cyan]Category[/cyan]", default=entry.get("category", "other"))
    tags_raw = Prompt.ask("[cyan]Tags[/cyan]", default=", ".join(entry.get("tags", [])))
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    console.print(f"[dim]Current content:[/dim]\n{entry['content']}\n")
    if Confirm.ask("Replace content?", default=False):
        console.print("[dim]New content (end with a blank line):[/dim]")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        content = "\n".join(lines)
    else:
        content = entry["content"]

    lore_store.update(entry_id, title=title, content=content, category=category, tags=tags)
    console.print(f"\n[green]Updated[/green] [{entry_id}]")


@app.command("delete")
def delete_entry(entry_id: str = typer.Argument(...)):
    """Delete a lore entry."""
    entry = lore_store.get(entry_id)
    if not entry:
        console.print(f"[red]No entry with ID '{entry_id}'[/red]")
        raise typer.Exit(1)

    if Confirm.ask(f"Delete [cyan]{entry['title']}[/cyan]?"):
        lore_store.delete(entry_id)
        console.print("[green]Deleted.[/green]")


@app.command("preview")
def preview_entry(entry_id: str = typer.Argument(...)):
    """Preview how a lore entry will appear."""
    entry = lore_store.get(entry_id)
    if not entry:
        console.print(f"[red]No entry with ID '{entry_id}'[/red]")
        raise typer.Exit(1)

    console.print(
        Panel(
            entry["content"],
            title=f"[bold cyan]{entry['title']}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
