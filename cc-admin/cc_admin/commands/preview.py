import re

import typer
from rich.console import Console
from rich.panel import Panel

from cc_admin import builder, config
from cc_admin.commands.scan import load_cache

app = typer.Typer(help="Simulate a heybabb response before publishing")
console = Console()

_WORKING_ON = {"working on", "now", "current", "doing", "latest"}
_TOOLS_KW = {"tools", "products", "built", "projects", "building"}
_STATUS_KW = {"status", "shipped", "released", "releases"}
_VISION_KW = {"vision", "future", "direction", "roadmap", "goal", "headed"}


@app.callback(invoke_without_command=True)
def preview(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Query to simulate"),
):
    if ctx.invoked_subcommand:
        return

    admin_cfg = config.load_admin_config()

    try:
        scan_results = load_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    knowledge = builder.build_knowledge(scan_results, admin_cfg)

    console.print(f"\n[dim]Simulating: '{query}'[/dim]\n")
    _route(query, knowledge)


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())


def _match(query: str, candidates: list[str]) -> bool:
    q = set(_normalize(query).split())
    for c in candidates:
        c_words = set(_normalize(c).split())
        if c_words and len(q & c_words) / len(c_words) >= 0.5:
            return True
    return False


def _route(query: str, knowledge: dict):
    eggs = knowledge.get("easter_eggs", [])
    for egg in eggs:
        t = _normalize(egg["trigger"])
        q = _normalize(query)
        if t in q or all(w in q.split() for w in t.split()):
            console.print(Panel(egg["response"], title="[dim]easter egg[/dim]", border_style="yellow"))
            return

    for pair in knowledge.get("qa", []):
        if _match(query, [pair["question"]] + pair.get("variants", [])):
            console.print(Panel(_render_answer(pair["answer"], knowledge), title="[dim]qa match[/dim]", border_style="green"))
            return

    q = query.lower()
    for tool in knowledge["tools"]:
        if tool["id"].lower() in q or any(a.lower() in q for a in tool.get("aliases", [])):
            _show_tool(tool)
            return

    if any(kw in q for kw in _VISION_KW):
        roadmap = knowledge.get("roadmap", "")
        console.print(Panel(roadmap or "[dim]No roadmap set.[/dim]", title="[dim]vision[/dim]", border_style="cyan"))
        return

    if any(kw in q for kw in _WORKING_ON | _STATUS_KW):
        _show_now(knowledge)
        return

    if any(kw in q for kw in _TOOLS_KW):
        _show_tools(knowledge)
        return

    console.print("[dim]→ not_found: 'I don't have that indexed yet.'[/dim]")


def _render_answer(answer: str, knowledge: dict) -> str:
    answer = answer.replace("{{org}}", knowledge.get("org", ""))
    answer = answer.replace("{{tool_count}}", str(len(knowledge.get("tools", []))))
    return answer


def _show_tool(tool: dict):
    slots = tool.get("knowledge", {})
    meta = tool.get("slot_meta", {})
    body = ""
    for label, key in (("Summary", "summary"), ("Problem", "problem"), ("Status", "status")):
        val = slots.get(key, "")
        if val:
            if meta.get(key, {}).get("confidence") == "speculative":
                body += f"[bold]{label}[/bold] [dim italic](we're still figuring this out)[/dim italic]\n{val[:200]}…\n\n"
            else:
                body += f"[bold]{label}[/bold]\n{val[:200]}…\n\n"
    console.print(Panel(body.strip() or "[dim]empty[/dim]", title=f"[dim]tool: {tool['id']}[/dim]", border_style="cyan"))


def _show_now(knowledge: dict):
    now = knowledge.get("now", "").replace("# Now\n", "").strip()
    announcement = knowledge.get("announcement", "")
    body = ""
    if announcement:
        body += f"[bold yellow]{announcement}[/bold yellow]\n\n"
    body += now[:300] if now else "[dim]No NOW.md content.[/dim]"
    console.print(Panel(body, title="[dim]now[/dim]", border_style="cyan"))


def _show_tools(knowledge: dict):
    tools = knowledge.get("tools", [])
    body = "\n".join(f"  [cyan]{t['id']}[/cyan]" for t in tools) or "[dim]none[/dim]"
    console.print(Panel(body, title="[dim]tools list[/dim]", border_style="cyan"))
