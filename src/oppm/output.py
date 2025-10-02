from rich.console import Console
from rich.table import Table

console = Console()


def success(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}✅  {message}{post}", style="bold green")


def error(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}❌  {message}{post}", style="bold red")


def warning(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}⚠️  {message}{post}", style="bold yellow")


def info(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}ℹ️  {message}{post}", style="cyan")


def step(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}📦  {message}{post}", style="blue")


def debug(message: str, pre: str = "", post: str = "") -> None:
    console.print(f"{pre}🔍  {message}{post}", style="dim")


def create_table(title: str, *columns: str) -> Table:
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column, style="cyan")
    return table
