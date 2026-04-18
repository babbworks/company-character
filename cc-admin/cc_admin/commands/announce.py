import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from cc_admin import announce_store

app = typer.Typer(help="Manage pinned announcements")
console = Console()


@app.command("list")
def list_announcements():
    """List all announcements."""
    items = announce_store.all_announcements()
    if not items:
        console.print("[dim]No announcements.[/dim]")
        return

    table = Table(show_lines=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Active")
    table.add_column("Expires")
    table.add_column("Created")
    table.add_column("Message", max_width=60)

    for item in reversed(items):
        active = "[green]yes[/green]" if item.get("active") else "[dim]no[/dim]"
        table.add_row(
            item["id"],
            active,
            item.get("expires") or "—",
            item.get("created", ""),
            item["message"][:80] + ("…" if len(item["message"]) > 80 else ""),
        )
    console.print(table)

    current = announce_store.active()
    if current:
        console.print(f"\n[bold]Active:[/bold] {current['message']}")
    else:
        console.print("\n[dim]No active announcement.[/dim]")


@app.command("set")
def set_announcement(
    message: str = typer.Argument(None, help="Announcement text — omit for interactive prompt"),
    expires: str = typer.Option(None, "--expires", help="ISO date e.g. 2026-05-01"),
):
    """Set a new active announcement, replacing any existing one."""
    if not message:
        message = Prompt.ask("[cyan]Announcement[/cyan]")
        expires = Prompt.ask("[cyan]Expires[/cyan] [dim](ISO date or blank for no expiry)[/dim]", default="") or None

    item = announce_store.set_announcement(message, expires)
    console.print(f"[green]Announcement set[/green] [{item['id']}]")
    if expires:
        console.print(f"[dim]Expires: {expires}[/dim]")


@app.command("clear")
def clear_announcements():
    """Deactivate all announcements."""
    count = announce_store.clear()
    console.print(f"[green]Cleared[/green] {count} active announcement(s).")


@app.command("expire")
def expire_old():
    """Deactivate announcements past their expiry date."""
    count = announce_store.expire_old()
    if count:
        console.print(f"[green]Expired[/green] {count} announcement(s).")
    else:
        console.print("[dim]Nothing to expire.[/dim]")
