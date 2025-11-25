"""Provider management commands."""

import click
from rich.console import Console
from rich.table import Table

from giskit.providers.base import list_providers

console = Console()


@click.group()
def providers() -> None:
    """Manage and query data providers."""
    pass


@providers.command("list")
def list_cmd() -> None:
    """List all available data providers.

    Examples:
        giskit providers list
    """
    provider_list = list_providers()

    if not provider_list:
        console.print("[yellow]No providers registered[/yellow]")
        console.print("[dim]Providers will be registered in Phase 2[/dim]")
        return

    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")

    for provider in sorted(provider_list):
        table.add_row(provider, "✓")

    console.print(table)


@providers.command("info")
@click.argument("provider_name")
def info(provider_name: str) -> None:
    """Show detailed information about a provider.

    Examples:
        giskit providers info pdok
        giskit providers info osm
    """
    # TODO: Implement provider metadata retrieval
    console.print(f"[bold]Provider:[/bold] {provider_name}")
    console.print("[yellow]Provider metadata not yet implemented[/yellow]")
    console.print("[dim]Implementation coming in Phase 2[/dim]")
