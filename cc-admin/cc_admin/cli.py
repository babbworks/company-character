import typer
from rich.console import Console

from cc_admin.commands import (
    alias, announce, audit_cmd, build, diff, init,
    lore, override, persona, preview, publish, qa, repo, scan,
)

app = typer.Typer(
    name="cc-admin",
    help="company-character admin — compile and manage your organisation's knowledge base.",
    no_args_is_help=True,
)

console = Console()

app.add_typer(init.app, name="init")
app.add_typer(scan.app, name="scan")
app.add_typer(build.app, name="build")
app.add_typer(diff.app, name="diff")
app.add_typer(publish.app, name="publish")
app.add_typer(qa.app, name="qa")
app.add_typer(override.app, name="override")
app.add_typer(lore.app, name="lore")
app.add_typer(announce.app, name="announce")
app.add_typer(alias.app, name="alias")
app.add_typer(persona.app, name="persona")
app.add_typer(repo.app, name="repo")
app.add_typer(preview.app, name="preview")
app.add_typer(audit_cmd.app, name="audit")


@app.command()
def info():
    """Show current config and paths."""
    from cc_admin import config

    admin_cfg = config.load_admin_config()
    console.print(f"[bold]Org:[/bold]      {admin_cfg['org']}")
    console.print(f"[bold]Brand:[/bold]    {admin_cfg.get('brand', '—')}")
    console.print(f"[bold]State:[/bold]    {config.state_path(admin_cfg).resolve()}")
    console.print(f"[bold]Dist:[/bold]     {config.dist_path(admin_cfg).resolve()}")
    console.print(f"[bold]CLI:[/bold]      {config.cli_path(admin_cfg).resolve()}")
    console.print(f"[bold]Overrides:[/bold] {config.overrides_path().resolve()}")
