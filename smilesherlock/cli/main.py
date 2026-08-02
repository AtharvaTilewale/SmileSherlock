"""
Main CLI application for SmileSherlock.

Commands for SMILES lookup, structure download, batch processing, and more.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smilesherlock import __version__
from smilesherlock.config import settings
from smilesherlock.logging_config import logger

# Initialize CLI app with rich support
app = typer.Typer(
    name="smilesherlock",
    help="High-performance SMILES validation and PubChem lookup",
    no_args_is_help=True,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
) -> None:
    """
    SmileSherlock - SMILES validation and PubChem lookup tool.

    Visit: https://github.com/yourusername/SmileSherlock
    """
    if version:
        console.print(
            Panel(
                f"[bold cyan]SmileSherlock[/bold cyan] v{__version__}",
                expand=False,
            )
        )
        raise typer.Exit()


@app.command()
def status() -> None:
    """
    Show current configuration and system status.

    Displays cache directories, database status, and settings.
    """
    console.print(Panel("[bold cyan]SmileSherlock Status[/bold cyan]", expand=False))

    # Configuration table
    config_table = Table(title="Configuration", show_header=True)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("Cache Dir", str(settings.cache_dir))
    config_table.add_row("Data Dir", str(settings.data_dir))
    config_table.add_row("Log Dir", str(settings.log_dir))
    config_table.add_row("Database", str(settings.db_path))
    config_table.add_row("PubChem URL", settings.pubchem_base_url)
    config_table.add_row("Max Workers", str(settings.max_workers))
    config_table.add_row("Batch Size", str(settings.batch_size))
    config_table.add_row("Caching Enabled", str(settings.enable_cache))

    console.print(config_table)

    # Check database status
    if settings.db_path.exists():
        db_size = settings.db_path.stat().st_size / 1024 / 1024  # MB
        console.print(f"[green]✓[/green] Database exists ({db_size:.2f} MB)")
    else:
        console.print("[yellow]⚠[/yellow] Database not yet created")

    # Check directories
    for directory in [settings.cache_dir, settings.data_dir, settings.log_dir]:
        if directory.exists():
            console.print(f"[green]✓[/green] {directory.name} exists")
        else:
            console.print(f"[yellow]⚠[/yellow] {directory.name} missing")


@app.command()
def init() -> None:
    """
    Initialize SmileSherlock directories and database.

    Creates cache, data, and log directories if they don't exist.
    Initializes the SQLite database schema.
    """
    console.print(Panel("[bold cyan]Initializing SmileSherlock[/bold cyan]", expand=False))

    try:
        # Directories are created automatically by settings
        console.print(f"[green]✓[/green] Cache directory: {settings.cache_dir}")
        console.print(f"[green]✓[/green] Data directory: {settings.data_dir}")
        console.print(f"[green]✓[/green] Log directory: {settings.log_dir}")

        # Database initialization (placeholder for phase 2)
        console.print(f"[yellow]→[/yellow] Database schema will be created in Phase 2")
        console.print(f"   Location: {settings.db_path}")

        logger.info("SmileSherlock initialized successfully")
        console.print("\n[green bold]✓ Initialization complete![/green bold]")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """
    Display version information.
    """
    console.print(f"SmileSherlock version {__version__}")
    console.print("License: MIT")
    console.print("Repository: https://github.com/yourusername/SmileSherlock")


# Placeholder commands for future phases (will be implemented progressively)
@app.command()
def lookup(
    smiles: str = typer.Argument(..., help="SMILES string to lookup"),
    cid: bool = typer.Option(False, "--cid", help="Treat input as CID instead of SMILES"),
) -> None:
    """
    Lookup a single compound in PubChem.

    Args:
        smiles: SMILES string or CID to lookup
        cid: If true, treat input as CID

    Example:
        smilesherlock lookup "c1ccccc1"
        smilesherlock lookup 5282253 --cid
    """
    console.print(
        Panel(
            "[bold yellow]Feature coming in Phase 2[/bold yellow]\n"
            "Implement PubChem lookup and SMILES validation",
            expand=False,
        )
    )


@app.command()
def batch(
    input_file: Path = typer.Argument(
        ...,
        help="Input file (CSV, TSV, XLSX, SMI, SDF)",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, xlsx, json)"),
) -> None:
    """
    Process a batch of SMILES from file.

    Args:
        input_file: File containing SMILES/structures
        output_file: Where to save results
        format: Output format (csv, xlsx, json)

    Example:
        smilesherlock batch compounds.csv --output results.xlsx --format xlsx
    """
    console.print(
        Panel(
            "[bold yellow]Feature coming in Phase 2-3[/bold yellow]\n"
            "Implement batch processing with multiple input/output formats",
            expand=False,
        )
    )


@app.command()
def download(
    cid: int = typer.Argument(..., help="PubChem CID"),
    format: str = typer.Option("sdf", "--format", "-f", help="Structure format (sdf, mol, pdb, png)"),
    dimension: str = typer.Option("3d", "--3d/--2d", help="2D or 3D structure"),
) -> None:
    """
    Download a chemical structure from PubChem.

    Args:
        cid: PubChem Compound ID
        format: Output format
        dimension: 2D or 3D structure

    Example:
        smilesherlock download 5282253 --format sdf --3d
    """
    console.print(
        Panel(
            "[bold yellow]Feature coming in Phase 3[/bold yellow]\n"
            "Implement structure download with multiple formats",
            expand=False,
        )
    )


if __name__ == "__main__":
    app()
