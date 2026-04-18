import re

from rich.console import Console
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def _brand(knowledge: dict) -> str:
    return knowledge.get("brand", knowledge.get("org", ""))


def _slot(tool: dict, key: str) -> str:
    return tool.get("knowledge", {}).get(key, "").strip()


def _is_speculative(tool: dict, key: str) -> bool:
    return tool.get("slot_meta", {}).get(key, {}).get("confidence") == "speculative"


def _signals_line(tool: dict) -> str:
    s = tool.get("signals", {})
    parts = []
    if s.get("last_commit"):
        parts.append(f"last commit {s['last_commit']}")
    if s.get("commits_7d") is not None:
        parts.append(f"{s['commits_7d']} commits this week")
    if s.get("open_prs"):
        parts.append(f"{s['open_prs']} open PR{'s' if s['open_prs'] != 1 else ''}")
    if s.get("recent_releases"):
        parts.append(f"latest release {s['recent_releases'][0]}")
    return "  ".join(parts)


def greeting(knowledge: dict):
    brand = _brand(knowledge)
    org = knowledge.get("org", "")
    console.print(
        Panel(
            f"[bold]Hey. I'm {brand}.[/bold]\n\n"
            f"I know what {org} is building, why, and where it's headed.\n"
            f"Ask me anything — or try [cyan]{brand.lower()} tools[/cyan] to start.",
            title=f"[bold cyan]{brand}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def tools_list(knowledge: dict):
    tools = knowledge.get("tools", [])
    if not tools:
        console.print("[dim]No tools indexed yet.[/dim]")
        return

    console.print(f"\n[bold]Tools — {knowledge.get('org', '')}[/bold]\n")
    for tool in tools:
        summary = _slot(tool, "summary")
        first_sentence = re.split(r"(?<=[.!?])\s", summary)[0] if summary else "[dim]no summary[/dim]"
        status = _slot(tool, "status")
        status_short = re.split(r"[.\n]", status)[0] if status else ""
        console.print(f"  [cyan bold]{tool['id']}[/cyan bold]")
        console.print(f"  {first_sentence}")
        if status_short:
            console.print(f"  [dim]{status_short}[/dim]")
        console.print()


def tool_detail(tool: dict):
    sections = [
        ("summary", None),
        ("The Problem", "problem"),
        ("How it Works", "how"),
        ("Status", "status"),
        ("Vision", "vision"),
        ("Industry Context", "context"),
    ]
    renderables = []
    for label, key in sections:
        if key is None:
            content = _slot(tool, "summary")
            if content:
                renderables.append(Markdown(content))
        else:
            content = _slot(tool, key)
            if not content:
                continue
            speculative = _is_speculative(tool, key)
            prefix = f"## {label}" + (" *(still figuring this out)*" if speculative else "")
            renderables.append(Markdown(f"{prefix}\n\n{content}"))

    signals = _signals_line(tool)
    if signals:
        renderables.append(f"[dim]{signals}[/dim]")

    console.print(
        Panel(
            Group(*renderables),
            title=f"[bold cyan]{tool['id']}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def working_on(knowledge: dict):
    from babb import knowledge as k

    announcement = knowledge.get("announcement")
    now = knowledge.get("now", "").replace("# Now\n", "").strip()
    brand = _brand(knowledge)
    top = k.active_tools(knowledge)
    releases = k.recent_releases(knowledge)

    body = ""
    if announcement:
        body += f"[bold yellow]{announcement}[/bold yellow]\n\n"
    if now:
        body += f"{now}\n\n"

    active = [t for t in top if t.get("signals", {}).get("commits_7d", 0) > 0]
    if active:
        body += "[bold]Most active this week[/bold]\n"
        for tool in active[:3]:
            c = tool["signals"]["commits_7d"]
            prs = tool["signals"].get("open_prs", 0)
            pr_str = f", {prs} open PR{'s' if prs != 1 else ''}" if prs else ""
            body += f"  [cyan]{tool['id']}[/cyan] — {c} commit{'s' if c != 1 else ''}{pr_str}\n"
        body += "\n"

    if releases:
        body += "[bold]Recent releases[/bold]\n"
        for tool_id, tag in releases[:4]:
            body += f"  [cyan]{tool_id}[/cyan] {tag}\n"

    if not body.strip():
        body = "Nothing indexed yet."

    console.print(Panel(body.strip(), title=f"[bold cyan]{brand}[/bold cyan] — now", border_style="cyan", padding=(1, 2)))


def lore_entry(entry: dict):
    console.print(
        Panel(Markdown(entry["content"]), title=f"[bold cyan]{entry['title']}[/bold cyan]", border_style="cyan", padding=(1, 2))
    )


def not_found(query: str = ""):
    console.print("[dim]I don't have that indexed yet.[/dim]")


def no_knowledge():
    console.print("[yellow]No knowledge base found.[/yellow] Run [cyan]cc-admin publish[/cyan] to generate one.")
