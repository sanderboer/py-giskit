"""Quirks management commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from giskit.protocols.quirks import KNOWN_QUIRKS, get_quirks

console = Console()


@click.group()
def quirks() -> None:
    """View and manage API quirks."""
    pass


@quirks.command("list")
def list_cmd() -> None:
    """List all known provider quirks.

    Examples:
        giskit quirks list
    """
    if not KNOWN_QUIRKS:
        console.print("[yellow]No quirks registered[/yellow]")
        return

    table = Table(title="Known API Quirks")
    table.add_column("Provider", style="cyan")
    table.add_column("Protocol", style="blue")
    table.add_column("Quirks", style="yellow")

    for provider, protocols in sorted(KNOWN_QUIRKS.items()):
        for protocol, quirk_obj in sorted(protocols.items()):
            # Count active quirks
            active_quirks = []
            if quirk_obj.requires_trailing_slash:
                active_quirks.append("trailing_slash")
            if quirk_obj.require_format_param:
                active_quirks.append("format_param")
            if quirk_obj.max_features_limit:
                active_quirks.append(f"max_limit={quirk_obj.max_features_limit}")
            if quirk_obj.custom_timeout:
                active_quirks.append(f"timeout={quirk_obj.custom_timeout}s")
            if quirk_obj.custom_headers:
                active_quirks.append(f"headers({len(quirk_obj.custom_headers)})")

            quirks_str = ", ".join(active_quirks) if active_quirks else "[dim]none[/dim]"
            table.add_row(provider, protocol, quirks_str)

    console.print(table)


@quirks.command("show")
@click.argument("provider")
@click.argument("protocol")
def show(provider: str, protocol: str) -> None:
    """Show detailed quirks for a specific provider/protocol.

    Examples:
        giskit quirks show pdok ogc-features
    """
    quirk_obj = get_quirks(provider, protocol)

    # Check if this is a known quirk configuration
    is_known = provider in KNOWN_QUIRKS and protocol in KNOWN_QUIRKS[provider]

    # Create panel title
    title = f"[bold]{provider}/{protocol}[/bold]"
    if not is_known:
        title += " [dim](using defaults)[/dim]"

    # Build quirks info
    info_lines = []

    # URL Quirks
    info_lines.append("[bold cyan]URL Quirks:[/bold cyan]")
    info_lines.append(f"  requires_trailing_slash: {quirk_obj.requires_trailing_slash}")

    # Parameter Quirks
    info_lines.append("\n[bold cyan]Parameter Quirks:[/bold cyan]")
    info_lines.append(f"  require_format_param: {quirk_obj.require_format_param}")
    if quirk_obj.require_format_param:
        info_lines.append(f"    param_name: {quirk_obj.format_param_name}")
        info_lines.append(f"    param_value: {quirk_obj.format_param_value}")
    info_lines.append(f"  max_features_limit: {quirk_obj.max_features_limit or 'none'}")

    # Timeout Quirks
    info_lines.append("\n[bold cyan]Timeout Quirks:[/bold cyan]")
    info_lines.append(f"  custom_timeout: {quirk_obj.custom_timeout or 'none'}")

    # Header Quirks
    info_lines.append("\n[bold cyan]Header Quirks:[/bold cyan]")
    if quirk_obj.custom_headers:
        for header, value in quirk_obj.custom_headers.items():
            info_lines.append(f"  {header}: {value}")
    else:
        info_lines.append("  [dim]none[/dim]")

    # Metadata
    if is_known:
        info_lines.append("\n[bold cyan]Metadata:[/bold cyan]")
        if quirk_obj.description:
            info_lines.append(f"  Description: {quirk_obj.description}")
        if quirk_obj.issue_url:
            info_lines.append(f"  Issue URL: {quirk_obj.issue_url}")
        if quirk_obj.workaround_date:
            info_lines.append(f"  Workaround Date: {quirk_obj.workaround_date}")

    console.print(Panel("\n".join(info_lines), title=title, border_style="blue"))


@quirks.command("monitor")
def monitor() -> None:
    """Show quirks usage statistics.

    Examples:
        giskit quirks monitor
    """
    from giskit.protocols.quirks_monitor import get_monitor

    monitor_obj = get_monitor()
    stats = monitor_obj.get_statistics()

    if not stats:
        console.print("[yellow]No quirks have been applied yet[/yellow]")
        console.print("[dim]Run some downloads first, then check monitor again[/dim]")
        return

    # Print report
    monitor_obj.print_report()
