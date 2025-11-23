"""GISKit CLI - Recipe-driven spatial data downloader.

Usage:
    giskit run recipe.json
    giskit validate recipe.json
    giskit providers list
    giskit providers info pdok
    giskit quirks list
    giskit quirks show pdok ogc-features
"""

import asyncio
import re
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from giskit import __version__
from giskit.core.recipe import Recipe
from giskit.protocols.quirks import KNOWN_QUIRKS, get_quirks
from giskit.providers.base import get_provider, list_providers

app = typer.Typer(
    name="giskit",
    help="Recipe-driven spatial data downloader for any location, any provider, anywhere",
    add_completion=False,
)
console = Console()


def _normalize_layer_name(name: str) -> str:
    """Normalize layer name to snake_case.

    Converts PascalCase/camelCase to snake_case for consistency.
    Examples:
        Perceel -> perceel
        BuildingPart -> building_part
        pand -> pand (already lowercase)
    """
    # Insert underscore before uppercase letters (but not at start)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters that follow lowercase
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    # Convert to lowercase
    return s2.lower()


async def _execute_recipe(recipe: Recipe, console: Console, verbose: bool):
    """Execute a recipe asynchronously.

    Args:
        recipe: Recipe to execute
        console: Rich console for output
        verbose: Verbose logging

    Returns:
        Dictionary mapping layer names to GeoDataFrames
    """
    import geopandas as gpd

    # Import provider module to register providers
    import giskit.providers.pdok  # noqa: F401

    # Get bbox from location
    with console.status("[bold green]Calculating bounding box..."):
        bbox = await recipe.get_bbox_wgs84()

    if verbose:
        console.print(f"  BBox (WGS84): {bbox}")

    # Download each dataset - store as separate layers
    layers = {}

    for i, dataset in enumerate(recipe.datasets, 1):
        console.print(f"\n[bold]Dataset {i}/{len(recipe.datasets)}:[/bold] {dataset.provider}")

        if dataset.service:
            console.print(f"  Service: {dataset.service}")
        if dataset.layers:
            console.print(f"  Layers: {', '.join(dataset.layers)}")

        try:
            # Get provider
            provider = get_provider(dataset.provider)

            # Convert bbox to Location for compatibility
            from giskit.core.recipe import Location, LocationType

            bbox_location = Location(type=LocationType.BBOX, value=list(bbox), crs="EPSG:4326")

            # Download dataset
            with console.status(f"[bold green]Downloading from {dataset.provider}..."):
                gdf = await provider.download_dataset(
                    dataset=dataset,
                    location=bbox_location,
                    output_path=recipe.output.path,
                    output_crs=recipe.output.crs,
                )

            if not gdf.empty:
                console.print(f"  [green]✓[/green] Downloaded {len(gdf)} features")

                # Store with layer name: service_layer or just service
                service = dataset.service or dataset.provider

                # Check if gdf has collection/layer information (from multi-layer downloads)
                if "_collection" in gdf.columns:
                    # Split by collection/layer
                    for collection_name in gdf["_collection"].unique():
                        layer_gdf = gdf[gdf["_collection"] == collection_name].copy()
                        # Normalize collection name to snake_case
                        normalized_name = _normalize_layer_name(collection_name)
                        full_layer_name = f"{service}_{normalized_name}"
                        layers[full_layer_name] = layer_gdf
                elif "_layer" in gdf.columns:
                    # Alternative layer column name
                    for layer_name in gdf["_layer"].unique():
                        layer_gdf = gdf[gdf["_layer"] == layer_name].copy()
                        # Normalize layer name to snake_case
                        normalized_name = _normalize_layer_name(layer_name)
                        full_layer_name = f"{service}_{normalized_name}"
                        layers[full_layer_name] = layer_gdf
                else:
                    # Single layer - use service name or first layer from request
                    if dataset.layers and len(dataset.layers) == 1:
                        layer_name = f"{service}_{dataset.layers[0]}"
                    else:
                        layer_name = service
                    layers[layer_name] = gdf
            else:
                console.print("  [yellow]No features found[/yellow]")

        except Exception as e:
            console.print(f"  [red]✗[/red] Failed: {e}")
            if verbose:
                console.print_exception()
            # Continue with other datasets

    # Add metadata layer if we have a bbox
    if layers and recipe.output.format.value == "gpkg":
        from datetime import datetime

        from shapely.geometry import Point

        from giskit.core.spatial import transform_bbox

        # Transform bbox to output CRS
        bbox_output_crs = transform_bbox(bbox, "EPSG:4326", recipe.output.crs)

        # Get center point
        center_x = (bbox_output_crs[0] + bbox_output_crs[2]) / 2
        center_y = (bbox_output_crs[1] + bbox_output_crs[3]) / 2

        # Build metadata dict - exact column order matching Sitedb
        metadata_dict = {
            "address": [None],
            "x": [center_x],
            "y": [center_y],
            "radius": [None],
            "bbox_minx": [bbox_output_crs[0]],
            "bbox_miny": [bbox_output_crs[1]],
            "bbox_maxx": [bbox_output_crs[2]],
            "bbox_maxy": [bbox_output_crs[3]],
            "download_date": [datetime.now().isoformat()],
            "crs": [recipe.output.crs],
            "grid_size": [None],  # For raster data, optional
            "bgt_layers": [None],  # Which BGT layers were requested
            "bag3d_lods": [None],  # Which BAG3D LOD levels were requested
        }

        # Add location-specific fields
        if recipe.location.type.value == "address":
            metadata_dict["address"] = [recipe.location.value]
            if recipe.location.radius is not None:
                metadata_dict["radius"] = [recipe.location.radius]
        elif recipe.location.type.value == "point":
            if recipe.location.radius is not None:
                metadata_dict["radius"] = [recipe.location.radius]

        # Extract dataset-specific metadata for traceability
        bgt_layers_list = []
        bag3d_lods_list = []

        for dataset in recipe.datasets:
            service = dataset.service or dataset.provider

            # Track BGT layers
            if service == "bgt" and dataset.layers:
                bgt_layers_list.extend(dataset.layers)

            # Track BAG3D LOD levels
            elif service == "bag3d" and dataset.layers:
                # Extract LOD levels (lod12 -> 1.2, lod13 -> 1.3, lod22 -> 2.2)
                for layer in dataset.layers:
                    if layer.startswith("lod"):
                        # Convert lod12 -> 1.2
                        lod_num = layer[3:]  # "12", "13", "22"
                        if len(lod_num) == 2:
                            lod_formatted = f"{lod_num[0]}.{lod_num[1]}"
                            bag3d_lods_list.append(lod_formatted)

            # Track grid_size if resolution is specified (for raster data)
            if dataset.resolution is not None:
                metadata_dict["grid_size"] = [dataset.resolution]

        # Store BGT layers (or "all" if many layers)
        if bgt_layers_list:
            # Sitedb uses "all" if all BGT layers are included
            if len(bgt_layers_list) > 40:  # Heuristic: if many layers, assume "all"
                metadata_dict["bgt_layers"] = ["all"]
            else:
                metadata_dict["bgt_layers"] = [",".join(sorted(bgt_layers_list))]

        # Store BAG3D LOD levels
        if bag3d_lods_list:
            metadata_dict["bag3d_lods"] = [",".join(sorted(bag3d_lods_list))]

        # Create metadata GeoDataFrame
        metadata_gdf = gpd.GeoDataFrame(
            metadata_dict, geometry=[Point(center_x, center_y)], crs=recipe.output.crs
        )

        layers["_metadata"] = metadata_gdf

    return layers if layers else None


@app.callback()
def main() -> None:
    """GISKit - Recipe-driven spatial data downloader."""
    pass


@app.command()
def version() -> None:
    """Show GISKit version."""
    console.print(f"GISKit version {__version__}")


@app.command()
def run(
    recipe_path: Path = typer.Argument(
        ..., help="Path to recipe JSON file", exists=True, dir_okay=False
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without downloading"),
) -> None:
    """Run a recipe to download spatial data.

    Examples:
        giskit run amsterdam.json
        giskit run --dry-run test.json
        giskit run --verbose utrecht.json
    """
    try:
        # Load recipe
        with console.status("[bold green]Loading recipe..."):
            recipe = Recipe.from_file(recipe_path)

        console.print(f"[bold green]✓[/bold green] Loaded recipe: {recipe.name or 'Unnamed'}")

        if recipe.description:
            console.print(f"  {recipe.description}")

        # Display recipe summary
        console.print(f"\n[bold]Location:[/bold] {recipe.location.type.value}")
        if recipe.location.type.value == "address":
            console.print(f"  Address: {recipe.location.value}")
            console.print(f"  Radius: {recipe.location.radius}m")
        elif recipe.location.type.value == "bbox":
            console.print(f"  BBox: {recipe.location.value}")

        console.print(f"\n[bold]Datasets:[/bold] {len(recipe.datasets)} datasets")
        for i, ds in enumerate(recipe.datasets, 1):
            console.print(f"  {i}. {ds.provider}", end="")
            if ds.service:
                console.print(f" → {ds.service}", end="")
            if ds.layers:
                console.print(f" → {', '.join(ds.layers)}", end="")
            console.print()

        console.print(f"\n[bold]Output:[/bold] {recipe.output.path}")
        console.print(f"  Format: {recipe.output.format.value}")
        console.print(f"  CRS: {recipe.output.crs}")

        # Convert dry_run to bool if it's a string (Typer bug workaround)
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() in ("true", "1", "yes")

        if dry_run:
            console.print("\n[yellow]Dry run - no data downloaded[/yellow]")
            return

        # Execute recipe
        console.print("\n[bold]Executing recipe...[/bold]")

        try:
            # Run async download - returns dict of layer_name -> GeoDataFrame
            layers = asyncio.run(_execute_recipe(recipe, console, verbose))

            # Save to output file
            if layers is not None and len(layers) > 0:
                output_path = recipe.output.path
                output_format = recipe.output.format.value

                with console.status(f"[bold green]Saving to {output_path}..."):
                    if output_format == "gpkg":
                        # Save each layer separately in GeoPackage
                        total_features = 0
                        for layer_name, gdf in layers.items():
                            # Remove internal columns before saving
                            save_gdf = gdf.copy()
                            for col in ["_provider", "_service", "_layer", "_collection"]:
                                if col in save_gdf.columns:
                                    save_gdf = save_gdf.drop(columns=[col])

                            save_gdf.to_file(output_path, driver="GPKG", layer=layer_name)
                            total_features += len(save_gdf)

                        console.print(
                            f"\n[bold green]✓[/bold green] Successfully saved {total_features} features in {len(layers)} layers to {output_path}"
                        )
                    elif output_format == "geojson":
                        # GeoJSON doesn't support layers - combine all
                        import geopandas as gpd

                        combined = gpd.GeoDataFrame(
                            gpd.pd.concat(layers.values(), ignore_index=True)
                        )
                        combined.to_file(output_path, driver="GeoJSON")
                        console.print(
                            f"\n[bold green]✓[/bold green] Successfully saved {len(combined)} features to {output_path}"
                        )
                    elif output_format == "shp":
                        # Shapefile doesn't support layers - combine all
                        import geopandas as gpd

                        combined = gpd.GeoDataFrame(
                            gpd.pd.concat(layers.values(), ignore_index=True)
                        )
                        combined.to_file(output_path, driver="ESRI Shapefile")
                        console.print(
                            f"\n[bold green]✓[/bold green] Successfully saved {len(combined)} features to {output_path}"
                        )
                    elif output_format == "fgb":
                        # FlatGeobuf doesn't support layers - combine all
                        import geopandas as gpd

                        combined = gpd.GeoDataFrame(
                            gpd.pd.concat(layers.values(), ignore_index=True)
                        )
                        combined.to_file(output_path, driver="FlatGeobuf")
                        console.print(
                            f"\n[bold green]✓[/bold green] Successfully saved {len(combined)} features to {output_path}"
                        )
            else:
                console.print("\n[yellow]No features downloaded[/yellow]")

        except Exception as download_error:
            console.print(f"\n[bold red]Download failed:[/bold red] {download_error}")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def validate(
    recipe_path: Path = typer.Argument(
        ..., help="Path to recipe JSON file", exists=True, dir_okay=False
    ),
) -> None:
    """Validate a recipe file without running it.

    Examples:
        giskit validate recipe.json
    """
    try:
        with console.status("[bold green]Validating recipe..."):
            recipe = Recipe.from_file(recipe_path)

        console.print("[bold green]✓[/bold green] Recipe is valid")
        console.print(f"  Name: {recipe.name or 'Unnamed'}")
        console.print(f"  Datasets: {len(recipe.datasets)}")
        console.print(f"  Output: {recipe.output.path}")

    except Exception as e:
        console.print("[bold red]✗[/bold red] Recipe validation failed")
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


providers_app = typer.Typer(help="Manage and query data providers")
app.add_typer(providers_app, name="providers")


@providers_app.command("list")
def providers_list() -> None:
    """List all available data providers.

    Examples:
        giskit providers list
    """
    providers = list_providers()

    if not providers:
        console.print("[yellow]No providers registered[/yellow]")
        console.print("[dim]Providers will be registered in Phase 2[/dim]")
        return

    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")

    for provider in sorted(providers):
        table.add_row(provider, "✓")

    console.print(table)


@providers_app.command("info")
def providers_info(
    provider_name: str = typer.Argument(..., help="Provider name (e.g., 'pdok')"),
) -> None:
    """Show detailed information about a provider.

    Examples:
        giskit providers info pdok
        giskit providers info osm
    """
    # TODO: Implement provider metadata retrieval
    console.print(f"[bold]Provider:[/bold] {provider_name}")
    console.print("[yellow]Provider metadata not yet implemented[/yellow]")
    console.print("[dim]Implementation coming in Phase 2[/dim]")


# Quirks commands
quirks_app = typer.Typer(help="View and manage API quirks")
app.add_typer(quirks_app, name="quirks")


@quirks_app.command("list")
def quirks_list() -> None:
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
        for protocol, quirks in sorted(protocols.items()):
            # Count active quirks
            active_quirks = []
            if quirks.requires_trailing_slash:
                active_quirks.append("trailing_slash")
            if quirks.require_format_param:
                active_quirks.append("format_param")
            if quirks.max_features_limit:
                active_quirks.append(f"max_limit={quirks.max_features_limit}")
            if quirks.custom_timeout:
                active_quirks.append(f"timeout={quirks.custom_timeout}s")
            if quirks.custom_headers:
                active_quirks.append(f"headers({len(quirks.custom_headers)})")

            quirks_str = ", ".join(active_quirks) if active_quirks else "[dim]none[/dim]"
            table.add_row(provider, protocol, quirks_str)

    console.print(table)


@quirks_app.command("show")
def quirks_show(
    provider: str = typer.Argument(..., help="Provider name (e.g., 'pdok')"),
    protocol: str = typer.Argument(..., help="Protocol name (e.g., 'ogc-features')"),
) -> None:
    """Show detailed quirks for a specific provider/protocol.

    Examples:
        giskit quirks show pdok ogc-features
    """
    quirks = get_quirks(provider, protocol)

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
    info_lines.append(f"  requires_trailing_slash: {quirks.requires_trailing_slash}")

    # Parameter Quirks
    info_lines.append("\n[bold cyan]Parameter Quirks:[/bold cyan]")
    info_lines.append(f"  require_format_param: {quirks.require_format_param}")
    if quirks.require_format_param:
        info_lines.append(f"    param_name: {quirks.format_param_name}")
        info_lines.append(f"    param_value: {quirks.format_param_value}")
    info_lines.append(f"  max_features_limit: {quirks.max_features_limit or 'none'}")

    # Timeout Quirks
    info_lines.append("\n[bold cyan]Timeout Quirks:[/bold cyan]")
    info_lines.append(f"  custom_timeout: {quirks.custom_timeout or 'none'}")

    # Header Quirks
    info_lines.append("\n[bold cyan]Header Quirks:[/bold cyan]")
    if quirks.custom_headers:
        for header, value in quirks.custom_headers.items():
            info_lines.append(f"  {header}: {value}")
    else:
        info_lines.append("  [dim]none[/dim]")

    # Metadata
    if is_known:
        info_lines.append("\n[bold cyan]Metadata:[/bold cyan]")
        if quirks.description:
            info_lines.append(f"  Description: {quirks.description}")
        if quirks.issue_url:
            info_lines.append(f"  Issue URL: {quirks.issue_url}")
        if quirks.workaround_date:
            info_lines.append(f"  Workaround Date: {quirks.workaround_date}")

    console.print(Panel("\n".join(info_lines), title=title, border_style="blue"))


@quirks_app.command("monitor")
def quirks_monitor() -> None:
    """Show quirks usage statistics.

    Examples:
        giskit quirks monitor
    """
    from giskit.protocols.quirks_monitor import get_monitor

    monitor = get_monitor()
    stats = monitor.get_statistics()

    if not stats:
        console.print("[yellow]No quirks have been applied yet[/yellow]")
        console.print("[dim]Run some downloads first, then check monitor again[/dim]")
        return

    # Print report
    monitor.print_report()


# Export commands
export_app = typer.Typer(help="Export GeoPackage to various formats")
app.add_typer(export_app, name="export")


@export_app.command("ifc")
def export_ifc(
    input_path: Path = typer.Argument(
        ..., help="Path to input GeoPackage file", exists=True, dir_okay=False
    ),
    output_path: Path = typer.Argument(..., help="Path to output IFC file"),
    ifc_version: str = typer.Option(
        "IFC4X3_ADD2", "--version", "-v", help="IFC schema version (IFC4X3_ADD2, IFC4, IFC2X3)"
    ),
    site_name: str = typer.Option("Site", "--site-name", "-s", help="Name for the IFC site"),
    absolute: bool = typer.Option(
        False, "--absolute", help="Use absolute RD coordinates (default: relative)"
    ),
    absolute_z: bool = typer.Option(
        False, "--absolute-z", help="Keep absolute NAP elevations (default: normalize to ground)"
    ),
    ref_x: Optional[float] = typer.Option(
        None, "--ref-x", help="Reference point X coordinate (auto-detect if not specified)"
    ),
    ref_y: Optional[float] = typer.Option(
        None, "--ref-y", help="Reference point Y coordinate (auto-detect if not specified)"
    ),
) -> None:
    """Export GeoPackage to IFC format.

    Examples:
        giskit export ifc input.gpkg output.ifc
        giskit export ifc --version IFC4 input.gpkg output.ifc
        giskit export ifc --site-name "Amsterdam Dam" input.gpkg output.ifc
        giskit export ifc --absolute --absolute-z input.gpkg output.ifc
    """
    try:
        from giskit.exporters.ifc import IFCExporter
    except ImportError:
        console.print("[bold red]Error:[/bold red] IfcOpenShell not installed")
        console.print("\nIFC export requires ifcopenshell.")
        console.print("\nInstall using pip:")
        console.print("  [bold]pip install giskit[ifc][/bold]")
        console.print("\nOr separately:")
        console.print("  [bold]pip install ifcopenshell[/bold]")
        raise typer.Exit(1)

    # Convert flags
    relative = not absolute
    normalize_z = not absolute_z

    try:
        console.print(f"[bold green]Exporting to IFC:[/bold green] {output_path}")
        console.print(f"  Input: {input_path}")
        console.print(f"  IFC Version: {ifc_version}")
        console.print(f"  Site Name: {site_name}")
        console.print(f"  Coordinate Mode: {'relative' if relative else 'absolute'}")
        console.print(f"  Z-Normalization: {'enabled' if normalize_z else 'disabled'}")
        console.print()

        # Create exporter
        exporter = IFCExporter(ifc_version=ifc_version, author="GISKit", organization="A190")

        # Export with progress
        with console.status("[bold green]Exporting layers..."):
            exporter.export(
                db_path=input_path,
                output_path=output_path,
                layers=None,  # Export all supported layers
                relative=relative,
                normalize_z=normalize_z,
                site_name=site_name,
                ref_x=ref_x,
                ref_y=ref_y,
            )

        console.print("\n[bold green]✓[/bold green] Export complete!")
        console.print(f"  Output: {output_path}")

        # Show file size
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            console.print(f"  Size: {size_mb:.1f} MB")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Export failed: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
