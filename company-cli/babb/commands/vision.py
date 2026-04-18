import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from babb import knowledge as k

app = typer.Typer(help="Where Babb Works is headed")
console = Console()


@app.callback(invoke_without_command=True)
def vision(ctx: typer.Context):
    if ctx.invoked_subcommand:
        return

    knowledge = k.load()
    roadmap = knowledge.get("roadmap", "").replace("# Roadmap\n", "").strip()

    if not roadmap:
        tool_visions = [
            (t["id"], t.get("knowledge", {}).get("vision", ""))
            for t in knowledge.get("tools", [])
            if t.get("knowledge", {}).get("vision")
        ]
        if not tool_visions:
            console.print("[dim]No roadmap or vision content indexed yet.[/dim]")
            return
        body = "\n\n".join(f"**{tid}**\n{v}" for tid, v in tool_visions)
        console.print(Panel(Markdown(body), title="[bold cyan]Babb — vision[/bold cyan]", border_style="cyan", padding=(1, 2)))
        return

    console.print(Panel(Markdown(roadmap), title="[bold cyan]Babb — where we're headed[/bold cyan]", border_style="cyan", padding=(1, 2)))
