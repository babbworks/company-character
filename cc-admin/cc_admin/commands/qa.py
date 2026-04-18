import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from cc_admin import qa_store

app = typer.Typer(help="Manage Q&A pairs")
console = Console()


@app.command("list")
def list_pairs(
    category: str = typer.Option(None, "--category", "-c"),
    tag: str = typer.Option(None, "--tag", "-t"),
):
    """List all Q&A pairs."""
    pairs = qa_store.all_pairs()
    if category:
        pairs = [p for p in pairs if p.get("category") == category]
    if tag:
        pairs = [p for p in pairs if tag in p.get("tags", [])]

    if not pairs:
        console.print("[dim]No Q&A pairs found.[/dim]")
        return

    table = Table(show_lines=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Question", style="cyan")
    table.add_column("Category")
    table.add_column("Mode")
    table.add_column("Answer", max_width=50)

    for p in pairs:
        table.add_row(
            p["id"],
            p["question"],
            p.get("category", ""),
            p.get("mode", "offline"),
            p["answer"][:80] + ("…" if len(p["answer"]) > 80 else ""),
        )
    console.print(table)


@app.command("add")
def add_pair():
    """Interactively create a new Q&A pair."""
    console.print("\n[bold]New Q&A pair[/bold]\n")

    question = Prompt.ask("[cyan]Question[/cyan]")
    answer = Prompt.ask("[cyan]Answer[/cyan]")

    variants_raw = Prompt.ask("[cyan]Alternate phrasings[/cyan] [dim](comma-separated, or leave blank)[/dim]", default="")
    variants = [v.strip() for v in variants_raw.split(",") if v.strip()]

    category = Prompt.ask("[cyan]Category[/cyan]", choices=["company", "tool", "vision", "personality"], default="company")
    tags_raw = Prompt.ask("[cyan]Tags[/cyan] [dim](comma-separated, or leave blank)[/dim]", default="")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    mode = Prompt.ask("[cyan]Mode[/cyan]", choices=["offline", "ai-enhanced", "both"], default="offline")
    author = Prompt.ask("[cyan]Author[/cyan]", default="")

    pair = qa_store.add(question, answer, variants, category, tags, mode, author)
    console.print(f"\n[green]Added[/green] [{pair['id']}] {pair['question']}")


@app.command("edit")
def edit_pair(pair_id: str = typer.Argument(..., help="Pair ID")):
    """Edit an existing Q&A pair."""
    pair = qa_store.get(pair_id)
    if not pair:
        console.print(f"[red]No pair with ID '{pair_id}'[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Editing [{pair_id}][/bold] — leave blank to keep current value\n")

    question = Prompt.ask(f"[cyan]Question[/cyan]", default=pair["question"])
    answer = Prompt.ask(f"[cyan]Answer[/cyan]", default=pair["answer"])
    variants_raw = Prompt.ask(
        "[cyan]Variants[/cyan]",
        default=", ".join(pair.get("variants", [])),
    )
    variants = [v.strip() for v in variants_raw.split(",") if v.strip()]
    category = Prompt.ask("[cyan]Category[/cyan]", default=pair.get("category", "company"))
    tags_raw = Prompt.ask("[cyan]Tags[/cyan]", default=", ".join(pair.get("tags", [])))
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    mode = Prompt.ask("[cyan]Mode[/cyan]", default=pair.get("mode", "offline"))

    qa_store.update(pair_id, question=question, answer=answer, variants=variants, category=category, tags=tags, mode=mode)
    console.print(f"\n[green]Updated[/green] [{pair_id}]")


@app.command("delete")
def delete_pair(pair_id: str = typer.Argument(..., help="Pair ID")):
    """Delete a Q&A pair."""
    pair = qa_store.get(pair_id)
    if not pair:
        console.print(f"[red]No pair with ID '{pair_id}'[/red]")
        raise typer.Exit(1)

    if Confirm.ask(f"Delete [cyan]{pair['question']}[/cyan]?"):
        qa_store.delete(pair_id)
        console.print("[green]Deleted.[/green]")


@app.command("test")
def test_pair(query: str = typer.Argument(..., help="Query to test matching")):
    """Simulate how a query would match against Q&A pairs."""
    pairs = qa_store.all_pairs()
    match = qa_store.match(query, pairs)

    if match:
        console.print(f"\n[green]Matched[/green] [{match['id']}]")
        console.print(f"[bold]Q:[/bold] {match['question']}")
        console.print(f"[bold]A:[/bold] {match['answer']}")
    else:
        console.print("[dim]No match — would fall through to keyword routing.[/dim]")


@app.command("export")
def export_pairs(output: str = typer.Option("qa-export.json", "--output", "-o")):
    """Export all pairs to a JSON file."""
    import json
    pairs = qa_store.all_pairs()
    with open(output, "w") as f:
        json.dump(pairs, f, indent=2)
    console.print(f"[green]Exported[/green] {len(pairs)} pair(s) → {output}")


@app.command("import")
def import_pairs(input_file: str = typer.Argument(..., help="JSON file to import")):
    """Import pairs from a JSON file (merges, skips duplicates by question)."""
    import json
    with open(input_file) as f:
        incoming = json.load(f)

    existing_questions = {p["question"].lower() for p in qa_store.all_pairs()}
    added = 0
    for p in incoming:
        if p["question"].lower() not in existing_questions:
            qa_store.add(
                p["question"], p["answer"],
                p.get("variants", []), p.get("category", "company"),
                p.get("tags", []), p.get("mode", "offline"), p.get("author", ""),
            )
            added += 1

    console.print(f"[green]Imported[/green] {added} new pair(s) (skipped {len(incoming) - added} duplicates)")
