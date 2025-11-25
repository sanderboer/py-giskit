"""Provider management commands."""

import json
from pathlib import Path

import click
import yaml
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


@providers.command("json")
@click.option(
    "--provider",
    "-p",
    help="Only include specific provider (default: all providers)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save to file instead of stdout",
)
def json_cmd(provider: str | None, output: str | None) -> None:
    """Generate complete recipe template with all providers and layers from YAML configs.

    This command reads the YAML configuration files and generates a comprehensive
    recipe template showing all available providers, their services, layers (where
    defined), and default options. Users can copy and edit this JSON to create
    custom recipes.

    Examples:
        giskit providers json
        giskit providers json -p pdok
        giskit providers json -p klimaateffectatlas -o climate_template.json
    """
    # Get config directory
    config_dir = Path(__file__).parent.parent.parent / "config" / "providers"

    if not config_dir.exists():
        console.print(f"[red]Error: Config directory not found: {config_dir}[/red]")
        return

    # Build recipe template
    recipe_template = {
        "name": "Complete Recipe Template - All Providers & Layers",
        "description": "Template showing all available providers, services, and layers from YAML configs. Edit this JSON to select only the data you need.",
        "location": {
            "type": "point",
            "value": [4.90098, 52.37092],
            "radius": 500,
            "crs": "EPSG:4326",
        },
        "datasets": [],
        "output": {
            "path": "output.gpkg",
            "format": "gpkg",
            "crs": "EPSG:28992",
            "overwrite": True,
        },
    }

    # Read all provider YAML files
    provider_files = sorted(config_dir.glob("*.yml"))

    for yaml_file in provider_files:
        provider_name = yaml_file.stem

        # Filter by provider if specified
        if provider and provider_name != provider:
            continue

        try:
            with open(yaml_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            provider_config = config.get("provider", {})
            services = config.get("services", {})

            # Add datasets for each service
            for service_id, service_config in sorted(services.items()):
                dataset_entry = {
                    "_provider": provider_config.get("title", provider_name),
                    "_service_title": service_config.get("title", service_id),
                    "_protocol": service_config.get("protocol", "unknown"),
                    "_category": service_config.get("category", "unknown"),
                    "provider": provider_name,
                    "service": service_id,
                }

                # Add layers if defined in YAML
                layers_config = service_config.get("layers")
                coverages_config = service_config.get("coverages")

                if layers_config:
                    if isinstance(layers_config, dict):
                        # WMTS/WCS style: dict of layer_id: layer_name
                        dataset_entry["layers"] = list(layers_config.keys())
                        dataset_entry["_available_layers"] = layers_config
                    elif isinstance(layers_config, list):
                        # List of layer names
                        dataset_entry["layers"] = layers_config
                    else:
                        dataset_entry["layers"] = []
                elif coverages_config:
                    # WCS coverages
                    if isinstance(coverages_config, dict):
                        dataset_entry["layers"] = list(coverages_config.keys())
                        dataset_entry["_available_coverages"] = coverages_config
                        dataset_entry["_note"] = "WCS - use coverage names as layers"
                    else:
                        dataset_entry["layers"] = []
                else:
                    # No layers in YAML - try to get common layer examples
                    common_layers = _get_service_layers(None, service_id, service_config)
                    if common_layers:
                        dataset_entry["layers"] = common_layers
                        dataset_entry["_note"] = "Common layers - see service API for full list"
                    else:
                        # No layers defined
                        protocol = service_config.get("protocol", "")
                        dataset_entry["layers"] = []
                        if protocol == "ogc-features":
                            dataset_entry[
                                "_note"
                            ] = "OGC Features - layers fetched dynamically from API collections"
                        elif protocol == "wfs":
                            dataset_entry["_note"] = "WFS - layers fetched dynamically from service"
                        elif protocol in ("csv", "gtfs"):
                            dataset_entry["_note"] = f"{protocol.upper()} - no layers needed"

                # Add service-specific defaults if present
                defaults = {}
                if service_config.get("tile_format"):
                    defaults["tile_format"] = service_config["tile_format"]
                if service_config.get("tile_matrix_set"):
                    defaults["tile_matrix_set"] = service_config["tile_matrix_set"]
                if service_config.get("format"):
                    defaults["format"] = service_config["format"]

                if defaults:
                    dataset_entry["_defaults"] = defaults

                recipe_template["datasets"].append(dataset_entry)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {yaml_file.name}: {e}[/yellow]")
            continue

    if not recipe_template["datasets"]:
        console.print("[yellow]No datasets found[/yellow]")
        if provider:
            console.print(f"Provider '{provider}' not found or has no services")
        return

    # Output JSON
    json_str = json.dumps(recipe_template, indent=2, ensure_ascii=False)

    if output:
        output_path = Path(output)
        output_path.write_text(json_str, encoding="utf-8")
        console.print(f"[green]✓[/green] Recipe template saved to: {output}")
        console.print(f"  Providers: {len({d['provider'] for d in recipe_template['datasets']})}")
        console.print(f"  Services: {len(recipe_template['datasets'])}")
        console.print()
        console.print("[dim]Edit the JSON to select only the datasets you need,[/dim]")
        console.print("[dim]then run: giskit run {output}[/dim]")
    else:
        print(json_str)


def _get_service_layers(provider, service_id: str, service_info: dict) -> list[str]:
    """Get available layers for a service with default values.

    Args:
        provider: Provider instance
        service_id: Service identifier
        service_info: Service metadata

    Returns:
        List of layer names (or common examples for services without predefined layers)
    """
    # Common layer examples for frequently-used services (from recipe examples)
    COMMON_LAYERS = {
        # Base registers
        "bgt": ["pand", "wegdeel", "waterdeel"],
        "bag": ["pand", "verblijfsobject"],
        "brk": ["perceel"],
        "bestuurlijkegebieden": ["gemeenten", "provincies"],
        # CBS statistics
        "cbs-wijken-buurten-2024": ["buurten", "wijken"],
        "cbs-wijken-buurten-2023": ["buurten", "wijken"],
        "cbs-wijken-buurten-2022": ["buurten", "wijken"],
        "cbs-gebiedsindelingen": ["gemeenten", "provincies", "wijken", "buurten"],
        "cbs-vierkant-100m": ["vierkant100m"],
        "cbs-vierkant-500m": ["vierkant500m"],
        # Infrastructure
        "nwb-wegen": ["wegvakken"],
        "nwb-vaarwegen": ["vaarwegvakken"],
        "spoorwegen": ["spoorwegvakken"],
        # Topography
        "top10nl": ["wegdeel", "waterdeel", "gebouw"],
        # 3D
        "bag3d": ["lod22"],
        "3d-basisvoorziening": ["building"],
    }

    # Return common examples if available
    if service_id in COMMON_LAYERS:
        return COMMON_LAYERS[service_id]

    # For WCS/WMTS, layers are already handled by coverages/layers config
    # This is just a fallback
    return []
