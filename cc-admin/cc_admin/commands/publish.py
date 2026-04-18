import shutil

import typer
from rich.console import Console

from cc_admin import config

app = typer.Typer(help="Push dist/ to heybabb")
console = Console()


@app.callback(invoke_without_command=True)
def publish(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be copied without doing it"),
):
    if ctx.invoked_subcommand:
        return

    admin_cfg = config.load_admin_config()
    src = config.dist_path(admin_cfg) / "knowledge.json"
    cli = config.cli_path(admin_cfg)
    dest_dir = cli / "dist"
    dest = dest_dir / "knowledge.json"

    if not src.exists():
        console.print("[red]dist/knowledge.json not found. Run `cc-admin build` first.[/red]")
        raise typer.Exit(1)

    if not cli.exists():
        console.print(f"[red]babb-cli path not found: {cli}[/red]")
        raise typer.Exit(1)

    if dry_run:
        console.print(f"[dim]Would copy:[/dim] {src} → {dest}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    console.print(f"[green]Published[/green] → {dest}")
