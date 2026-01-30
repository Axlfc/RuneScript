"""CLI interface for Red-Green-Refactor IDE."""
import typer

app = typer.Typer(
    name="rgr",
    help="Red-Green-Refactor IDE - TDD with autonomous AI"
)

@app.command()
def init():
    """Initialize new project."""
    pass

@app.command()
def status():
    """Show project status."""
    pass

@app.command()
def nia_mode():
    """Launch nIA autonomous loop."""
    pass

if __name__ == "__main__":
    app()
