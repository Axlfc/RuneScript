"""CLI interface for Red-Green-Refactor IDE with nIA."""
import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from typing import Optional
import os

from src.generators.spec_generator import SpecGenerator
from src.generators.plan_generator import PlanGenerator
from src.core.loop_orchestrator import LoopOrchestrator
from src.core.plan_parser import PlanParser

app = typer.Typer(
    name="rgr",
    help="Red-Green-Refactor IDE - TDD with autonomous AI"
)
console = Console()

@app.command()
def init(
    prompt: str = typer.Argument(..., help="High-level project description"),
    name: str = typer.Option(None, "--name", "-n", help="Project name"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory")
):
    """Initialize new project from a single sentence."""
    project_path = path or Path.cwd()
    if name:
        project_path = project_path / name

    project_path.mkdir(parents=True, exist_ok=True)

    console.print(Panel(f"Initializing project in [bold cyan]{project_path}[/bold cyan]...", title="rgr init"))

    # 1. Generate SPEC.md
    console.print("Generating SPEC.md...")
    spec_gen = SpecGenerator()
    spec_content = spec_gen.generate(prompt)
    (project_path / "SPEC.md").write_text(spec_content)

    # 2. Generate IMPLEMENTATION_PLAN.md
    console.print("Generating IMPLEMENTATION_PLAN.md...")
    plan_gen = PlanGenerator()
    plan_content = plan_gen.generate(spec_content)
    (project_path / "IMPLEMENTATION_PLAN.md").write_text(plan_content)

    # 3. Copy NIA_PROMPT.md
    console.print("Creating NIA_PROMPT.md...")
    template_dir = Path(__file__).parent.parent / "templates"
    prompt_template = template_dir / "NIA_PROMPT.md.jinja2"
    if prompt_template.exists():
        # Simple copy for now, or could render if it had vars
        (project_path / "NIA_PROMPT.md").write_text(prompt_template.read_text())

    console.print("[bold green]Success![/bold green] Project initialized.")
    console.print("Run [bold cyan]rgr nia-mode[/bold cyan] to start building.")

@app.command()
def nia_mode(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    iterations: int = typer.Option(20, "--iterations", "-i", help="Max iterations")
):
    """Launch nIA autonomous loop."""
    project_path = path or Path.cwd()
    console.print(Panel(f"Launching nIA loop in [bold cyan]{project_path}[/bold cyan]", title="nIA Autonomous Mode"))

    orchestrator = LoopOrchestrator(project_path)

    def log_cb(msg: str):
        if "===" in msg:
            console.print(msg, style="bold yellow")
        elif "✅" in msg:
            console.print(msg, style="green")
        elif "❌" in msg:
            console.print(msg, style="bold red")
        else:
            console.print(msg)

    result = orchestrator.run(max_iterations=iterations, log_callback=log_cb)

    if result.status == "ALL_COMPLETE":
        console.print(Panel(result.message, title="Final Status", style="bold green"))
    elif result.status == "BLOCKED":
        console.print(Panel(result.message, title="Final Status", style="bold red"))
    else:
        console.print(Panel(result.message, title="Final Status", style="yellow"))

@app.command()
def status(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory")
):
    """Show project status."""
    project_path = path or Path.cwd()
    plan_path = project_path / "IMPLEMENTATION_PLAN.md"
    if not plan_path.exists():
        console.print(f"[red]IMPLEMENTATION_PLAN.md not found at {plan_path}.[/red]")
        return

    parser = PlanParser()
    tasks = parser.parse(plan_path)
    stats = parser.get_statistics(tasks)

    console.print(Panel(f"""
[bold]Project:[/bold] {project_path.name}
[bold]Progress:[/bold] {stats['percent']:.1f}% ({stats['completed']}/{stats['total']})

[green]Completed:[/green] {stats['completed']}
[yellow]Pending:[/yellow] {stats['remaining']}
[red]Blocked:[/red] {stats['blocked']}
""", title="rgr status"))

    if tasks:
        next_task = parser.find_next_pending(tasks)
        if next_task:
            console.print(f"\n[bold]Next Task:[/bold] {next_task.description}")
        else:
            console.print("\n[bold green]✅ All tasks complete![/bold green]")

if __name__ == "__main__":
    app()
