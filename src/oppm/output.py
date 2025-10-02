from rich.console import Console
from rich.table import Table

console = Console()


def success(message: str) -> None:
    console.print(f"✅ {message}", style="bold green")


def error(message: str) -> None:
    console.print(f"❌ {message}", style="bold red")


def warning(message: str) -> None:
    console.print(f"⚠️  {message}", style="bold yellow")


def info(message: str) -> None:
    console.print(f"ℹ️  {message}", style="cyan")


def step(message: str) -> None:
    console.print(f"📦 {message}", style="blue")


def debug(message: str) -> None:
    console.print(f"🔍 {message}", style="dim")


def create_table(title: str, *columns: str) -> Table:
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column, style="cyan")
    return table
