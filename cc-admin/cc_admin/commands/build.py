import typer
from rich.console import Console

from cc_admin import builder, config
from cc_admin.commands.scan import load_cache

app = typer.Typer(help="Compile scan cache into dist/knowledge.json")
console = Console()


@app.callback(invoke_without_command=True)
def build(ctx: typer.Context):
    if ctx.invoked_subcommand:
        return

    admin_cfg = config.load_admin_config()

    try:
        scan_results = load_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    with console.status("Building knowledge.json..."):
        knowledge = builder.build_knowledge(scan_results, admin_cfg)
        dest = builder.write_dist(knowledge, admin_cfg)

    console.print(f"[green]Built[/green] {len(knowledge['tools'])} tool(s) → [cyan]{dest}[/cyan]")
    for tool in knowledge["tools"]:
        filled = [k for k, v in tool["knowledge"].items() if v]
        console.print(f"  [dim]{tool['id']}[/dim] — slots: {', '.join(filled) or 'none'}")
