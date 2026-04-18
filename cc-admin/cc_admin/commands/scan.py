import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cc_admin import config, github_client, parser

app = typer.Typer(help="Scan babbworks GitHub org and parse repos")
console = Console()

_CACHE = Path(__file__).parent.parent.parent / "dist" / "scan-cache.json"


@app.callback(invoke_without_command=True)
def scan(
    ctx: typer.Context,
    save: bool = typer.Option(True, help="Save results to scan cache"),
    show: bool = typer.Option(True, help="Print summary table"),
):
    if ctx.invoked_subcommand:
        return

    admin_cfg = config.load_admin_config()
    state = config.load_state(admin_cfg)
    org = admin_cfg["org"]
    section_map = state["section_map"]
    topic_categories = state["topic_categories"]

    console.print(f"\n[bold]Scanning [cyan]{org}[/cyan]...[/bold]")

    repos = github_client.list_repos(org)
    opted_in = [r for r in repos if any(t in topic_categories for t in r.get("topics", []))]

    if not opted_in:
        console.print("[yellow]No repos with babb-* topics found.[/yellow]")
        raise typer.Exit()

    results = []
    with console.status("Fetching READMEs and signals..."):
        for repo in opted_in:
            name = repo["name"]
            topics = repo.get("topics", [])
            babb_topics = parser.babb_topics(topics)
            category = next(
                (topic_categories[t] for t in babb_topics if t in topic_categories),
                "tool",
            )
            readme = github_client.get_readme(org, name)
            slots = parser.parse_sections(readme, section_map) if readme else {}
            signals = github_client.get_signals(org, name)
            results.append(
                {
                    "name": name,
                    "babb_topics": babb_topics,
                    "category": category,
                    "slots": slots,
                    "signals": signals,
                }
            )

    if save:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"[dim]Saved to {_CACHE}[/dim]")

    if show:
        table = Table(title=f"{org} — scanned repos", show_lines=True)
        table.add_column("Repo", style="cyan")
        table.add_column("Topics")
        table.add_column("Slots found")
        table.add_column("Commits 7d", justify="right")
        table.add_column("Open PRs", justify="right")
        for r in results:
            table.add_row(
                r["name"],
                ", ".join(r["babb_topics"]),
                ", ".join(r["slots"].keys()) or "[dim]none[/dim]",
                str(r["signals"].get("commits_7d", 0)),
                str(r["signals"].get("open_prs", 0)),
            )
        console.print(table)

    return results


def load_cache() -> list[dict]:
    if not _CACHE.exists():
        raise FileNotFoundError("No scan cache found. Run `cc-admin scan` first.")
    with open(_CACHE) as f:
        return json.load(f)
