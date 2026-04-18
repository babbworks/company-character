import json
from pathlib import Path

import typer
from rich.console import Console

from cc_admin import builder, config
from cc_admin.commands.scan import load_cache

app = typer.Typer(help="Show what would change before publishing")
console = Console()


@app.callback(invoke_without_command=True)
def diff(ctx: typer.Context):
    if ctx.invoked_subcommand:
        return

    admin_cfg = config.load_admin_config()
    dist = config.dist_path(admin_cfg) / "knowledge.json"

    if not dist.exists():
        console.print("[yellow]No existing dist/knowledge.json — nothing to diff against.[/yellow]")
        raise typer.Exit()

    with open(dist) as f:
        current = json.load(f)

    try:
        scan_results = load_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    proposed = builder.build_knowledge(scan_results, admin_cfg)

    current_tools = {t["id"]: t for t in current.get("tools", [])}
    proposed_tools = {t["id"]: t for t in proposed.get("tools", [])}

    added = set(proposed_tools) - set(current_tools)
    removed = set(current_tools) - set(proposed_tools)
    changed = []

    for tid in set(current_tools) & set(proposed_tools):
        c = current_tools[tid]["knowledge"]
        p = proposed_tools[tid]["knowledge"]
        slot_diff = {}
        all_slots = set(c) | set(p)
        for slot in all_slots:
            if c.get(slot) != p.get(slot):
                slot_diff[slot] = {"from": c.get(slot, "[missing]"), "to": p.get(slot, "[missing]")}
        if slot_diff:
            changed.append((tid, slot_diff))

    if not added and not removed and not changed:
        console.print("[green]No changes.[/green]")
        return

    if added:
        console.print(f"\n[green]+ Added:[/green] {', '.join(added)}")
    if removed:
        console.print(f"[red]- Removed:[/red] {', '.join(removed)}")
    for tid, slots in changed:
        console.print(f"\n[cyan]~ {tid}[/cyan]")
        for slot, delta in slots.items():
            console.print(f"  [yellow]{slot}[/yellow]")
            console.print(f"  [dim]from:[/dim] {str(delta['from'])[:120]}")
            console.print(f"  [dim]  to:[/dim] {str(delta['to'])[:120]}")
