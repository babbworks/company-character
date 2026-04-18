import typer
from rich.console import Console
from rich.table import Table

from cc_admin import audit

app = typer.Typer(help="Show build audit log")
console = Console()


@app.callback(invoke_without_command=True)
def show_audit(
    ctx: typer.Context,
    last: int = typer.Option(10, "--last", "-n", help="Number of entries to show"),
):
    if ctx.invoked_subcommand:
        return

    entries = audit.all_entries()
    if not entries:
        console.print("[dim]No audit entries yet. Run `cc-admin build` first.[/dim]")
        return

    for entry in entries[-last:]:
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        op = entry.get("operation", "")
        repos = entry.get("repos", [])
        overrides = entry.get("overrides_applied", {})

        console.print(f"\n[dim]{ts}[/dim]  [bold]{op}[/bold]")
        if repos:
            console.print(f"  Repos: {', '.join(repos)}")
        if overrides:
            for repo, applied in overrides.items():
                for slot, action in applied.items():
                    console.print(f"  [yellow]{repo}/{slot}[/yellow] → {action}")
        else:
            console.print("  [dim]No overrides applied — all slots from README[/dim]")

        for repo in repos:
            sourced = entry.get(repo, {}).get("slots_sourced", {})
            if sourced:
                readme_slots = [k for k, v in sourced.items() if v == "readme"]
                if readme_slots:
                    console.print(f"  [dim]{repo} readme slots: {', '.join(readme_slots)}[/dim]")
