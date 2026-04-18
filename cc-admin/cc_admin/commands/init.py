"""
Scaffold a fresh company-state/ directory for a new organisation.
"""
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer(help="Scaffold a new company-state/ for your organisation")
console = Console()

_TEMPLATES = {
    "section-map.yml": """\
org: {org}

topic_categories:
  {prefix}-tool: tool
  {prefix}-featured: tool
  {prefix}-vision: vision
  {prefix}-internal: internal

section_map:
  "What is it?": summary
  "The Problem": problem
  "How it Works": how
  "Current Status": status
  "The Vision": vision
  "Industry Context": context
""",
    "personality.md": """\
# {brand} — Personality & Voice

{brand} is the public face of {org} in the terminal.

## Voice
- First person, present tense
- Short sentences. No filler.
- Knows a lot but admits when something is still being figured out

## Do
- Speak from what you know
- Reference specific tools by name

## Don't
- Use marketing language
- Pad responses

## Greeting
"Hey. I'm {brand}."

## When asked something outside the knowledge base
"I don't have that indexed yet."
""",
    "NOW.md": """\
# Now

Add a short statement here about what your team is working on right now.
""",
    "roadmap.md": """\
# Roadmap

## Now
Describe your current focus.

## Next
Describe what comes after.

## Later
Describe longer-term direction.
""",
    "response-templates.yml": """\
tool_summary: |
  {name} — {summary}
  Status: {status}

working_on: |
  {now_md}

  Most active this week: {active_repos}
  Recent releases: {recent_releases}

unknown: "I don't have that indexed yet."

greeting: "Hey. I'm {brand}. Ask me anything about {org}."
""",
}


@app.callback(invoke_without_command=True)
def init(
    ctx: typer.Context,
    output: str = typer.Option("../company-state", "--output", "-o", help="Where to create the state folder"),
):
    """Scaffold a new company-state/ directory."""
    if ctx.invoked_subcommand:
        return

    console.print("\n[bold]cc-admin init[/bold] — setting up a new company state\n")

    org = Prompt.ask("[cyan]GitHub org name[/cyan]", default="your-github-org")
    brand = Prompt.ask("[cyan]Brand / assistant name[/cyan]", default=org.capitalize())
    prefix = Prompt.ask("[cyan]GitHub topic prefix[/cyan] [dim](e.g. 'babb' → babb-tool, babb-featured)[/dim]", default=org.lower()[:8])

    dest = Path(output)
    if dest.exists() and any(dest.iterdir()):
        if not typer.confirm(f"\n{dest} already has files. Overwrite?", default=False):
            raise typer.Exit()

    dest.mkdir(parents=True, exist_ok=True)

    for filename, template in _TEMPLATES.items():
        content = template.replace("{org}", org).replace("{brand}", brand).replace("{prefix}", prefix)
        (dest / filename).write_text(content)
        console.print(f"  [green]created[/green] {dest / filename}")

    admin_config = {
        "org": org,
        "brand": brand,
        "state_path": str(dest.resolve()),
        "dist_path": "./dist",
        "cli_path": "../company-cli",
    }
    config_file = Path(__file__).parent.parent.parent / ".cc-admin.yml"
    with open(config_file, "w") as f:
        yaml.dump(admin_config, f, default_flow_style=False)

    console.print(f"\n[green]Done.[/green] Updated [cyan].cc-admin.yml[/cyan] with org: {org}")
    console.print(f"\nNext: add [cyan]{prefix}-tool[/cyan] topics to your repos, then run [cyan]cc-admin scan[/cyan]")
