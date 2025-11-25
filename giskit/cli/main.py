"""GISKit CLI - Recipe-driven spatial data downloader.

Usage:
    giskit run recipe.json
    giskit validate recipe.json
    giskit export ifc input.gpkg output.ifc
    giskit export glb input.ifc output.glb
    giskit providers list
    giskit providers info pdok
    giskit quirks list
    giskit quirks show pdok ogc-features
"""

import click
from rich.console import Console

from giskit import __version__
from giskit.cli.commands import export, providers, quirks, run, validate

console = Console()


@click.group()
@click.version_option(__version__, "-v", "--version", prog_name="giskit")
def cli() -> None:
    """GISKit - Recipe-driven spatial data downloader for any location, any provider, anywhere."""
    pass


# Add standalone commands
cli.add_command(run)
cli.add_command(validate)

# Add command groups
cli.add_command(export)
cli.add_command(providers)
cli.add_command(quirks)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
