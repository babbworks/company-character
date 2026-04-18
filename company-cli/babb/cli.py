import typer
from rich.console import Console

from babb import knowledge as k
from babb import responses
from babb.commands import ask, sync, vision

app = typer.Typer(
    help="Your organisation's CLI companion. Rename the entry point in pyproject.toml to match your brand.",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()

app.add_typer(ask.app, name="ask")
app.add_typer(sync.app, name="sync")
app.add_typer(vision.app, name="vision")


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        responses.greeting(k.load())


@app.command()
def tools():
    """List all indexed tools."""
    responses.tools_list(k.load())


@app.command()
def tool(name: str = typer.Argument(..., help="Tool name")):
    """Get the full breakdown of a specific tool."""
    knowledge = k.load()
    t = k.get_tool(knowledge, name)
    if not t:
        console.print(f"[dim]No tool named '{name}' in the index.[/dim]")
        raise typer.Exit(1)
    responses.tool_detail(t)


@app.command()
def now():
    """What the team is working on right now."""
    responses.working_on(k.load())


@app.command()
def version():
    """Show build info."""
    knowledge = k.load()
    built = knowledge.get("built_at", "unknown")
    tool_count = len(knowledge.get("tools", []))
    brand = knowledge.get("brand", knowledge.get("org", ""))
    console.print(f"[cyan]{brand}[/cyan]  |  {tool_count} tool(s) indexed  |  built {built[:10] if built else 'never'}")
