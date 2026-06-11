from rich.console import Console
from rich.theme import Theme

_THEME = Theme({
    "critical": "bold red",
    "high": "bold orange1",
    "medium": "bold yellow",
    "low": "bold green",
    "info": "cyan",
    "dim": "dim white",
})

console = Console(theme=_THEME)


def info(msg: str) -> None:
    console.print(f"[info]ℹ[/]  {msg}")


def success(msg: str) -> None:
    console.print(f"[low]✓[/]  {msg}")


def warn(msg: str) -> None:
    console.print(f"[medium]⚠[/]  {msg}")


def error(msg: str) -> None:
    console.print(f"[critical]✗[/]  {msg}")
