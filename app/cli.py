"""CLI to run the autonomous agent once."""

from __future__ import annotations

import uuid

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from app.agent.graph import run_agent
from app.config import get_settings

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def run(
    goal: str = typer.Argument(..., help="Goal for the autonomous agent"),
    thread_id: str | None = typer.Option(None, help="Continue an existing thread"),
) -> None:
    """Run one autonomous agent session and print the final answer."""
    settings = get_settings()
    tid = thread_id or str(uuid.uuid4())
    console.print(
        Panel.fit(
            f"[bold]model[/bold]: {settings.ollama_model}\n"
            f"[bold]thread[/bold]: {tid}\n"
            f"[bold]workspace[/bold]: {settings.agent_workspace}",
            title="Local LangGraph Agent",
        )
    )
    console.print(f"[cyan]Goal:[/cyan] {goal}\n")
    outcome = run_agent(goal, thread_id=tid, settings=settings)
    console.print(Markdown(outcome["result"]))
    console.print(f"\n[dim]thread_id={outcome['thread_id']}[/dim]")


@app.command("info")
def info() -> None:
    """Show current configuration."""
    settings = get_settings()
    console.print(
        {
            "ollama_base_url": settings.ollama_base_url,
            "ollama_model": settings.ollama_model,
            "workspace": str(settings.agent_workspace),
            "allow_shell": settings.agent_allow_shell,
            "max_iterations": settings.agent_max_iterations,
            "redis_url": settings.redis_url,
        }
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
