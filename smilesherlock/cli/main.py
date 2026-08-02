"""Main CLI application for SmileSherlock."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smilesherlock import __version__, lookup, validate_smiles
from smilesherlock.config import settings
from smilesherlock.core.database import DatabaseManager
from smilesherlock.logging_config import logger

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
    """SmileSherlock - SMILES validation and PubChem lookup tool."""
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
    """Show current configuration and system status."""
    console.print(Panel("[bold cyan]SmileSherlock Status[/bold cyan]", expand=False))
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

    if settings.db_path.exists():
        db_size = settings.db_path.stat().st_size / 1024 / 1024
        console.print(f"[green]✔[/green] Database exists ({db_size:.2f} MB)")
    else:
        console.print("[yellow]![/yellow] Database not yet created")

    for directory in [settings.cache_dir, settings.data_dir, settings.log_dir]:
        if directory.exists():
            console.print(f"[green]✔[/green] {directory.name} exists")
        else:
            console.print(f"[yellow]![/yellow] {directory.name} missing")


@app.command()
def init() -> None:
    """Initialize SmileSherlock directories and SQLite database schema."""
    console.print(Panel("[bold cyan]Initializing SmileSherlock[/bold cyan]", expand=False))
    try:
        console.print(f"[green]✔[/green] Cache directory: {settings.cache_dir}")
        console.print(f"[green]✔[/green] Data directory: {settings.data_dir}")
        console.print(f"[green]✔[/green] Log directory: {settings.log_dir}")

        db_mgr = DatabaseManager()
        db_mgr.init_db()
        console.print(f"[green]✔[/green] Database schema initialized at {settings.db_path}")

        logger.info("SmileSherlock initialized successfully")
        console.print("\n[green bold]✨ Initialization complete![/green bold]")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        console.print(f"[red]✖ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Display version information."""
    console.print(f"SmileSherlock version {__version__}")
    console.print("License: MIT")
    console.print("Repository: https://github.com/AtharvaTilewale/SmileSherlock")


@app.command()
def lookup_cmd(
    query: str = typer.Argument(..., help="SMILES string, CID, Name, InChI, or InChIKey"),
    cid: bool = typer.Option(False, "--cid", help="Treat input explicitly as PubChem CID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output result in JSON format"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable database caching"),
) -> None:
    """
    Lookup a single compound in PubChem.
    """
    search_type = "cid" if cid else "auto"

    if not cid and not query.isdigit():
        validation = validate_smiles(query)
        if not validation.is_valid and validation.error_message:
            console.print(f"[yellow]Note: SMILES parse warning: {validation.error_message}[/yellow]")

    with console.status(f"[bold green]Searching PubChem for '{query}'...[/bold green]"):
        result = lookup(query, search_type=search_type, use_cache=not no_cache)

    if not result:
        console.print(f"[red]✖ No compound found for: '{query}'[/red]")
        raise typer.Exit(code=1)

    if json_output:
        console.print_json(result.model_dump_json(exclude_none=True))
        return

    table = Table(title=f"Compound Details: {result.iupac_name or query}", show_header=True)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold white")

    table.add_row("PubChem CID", str(result.cid or "N/A"))
    table.add_row("IUPAC Name", result.iupac_name or "N/A")
    table.add_row("Molecular Formula", result.molecular_formula or "N/A")
    table.add_row("Molecular Weight", f"{result.molecular_weight:.4f} g/mol" if result.molecular_weight else "N/A")
    table.add_row("Canonical SMILES", result.canonical_smiles or "N/A")
    table.add_row("InChIKey", result.inchikey or "N/A")
    table.add_row("InChI", result.inchi or "N/A")
    table.add_row("XLogP", str(result.xlogp) if result.xlogp is not None else "N/A")
    table.add_row("H-Bond Donors", str(result.hbond_donor_count) if result.hbond_donor_count is not None else "N/A")
    table.add_row("H-Bond Acceptors", str(result.hbond_acceptor_count) if result.hbond_acceptor_count is not None else "N/A")

    console.print(table)


# Alias CLI app command
app.command(name="lookup")(lookup_cmd)


@app.command()
def batch(
    input_file: Path = typer.Argument(..., help="Input file (CSV, TSV, XLSX, SMI, SDF)"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, xlsx, json)"),
) -> None:
    """Process a batch of SMILES from file."""
    console.print(
        Panel(
            "[bold yellow]Feature coming in Phase 3[/bold yellow]\nBatch processing with file I/O",
            expand=False,
        )
    )


@app.command()
def download(
    cid: int = typer.Argument(..., help="PubChem CID"),
    format: str = typer.Option("sdf", "--format", "-f", help="Structure format (sdf, mol, pdb, png)"),
    dimension: str = typer.Option("3d", "--3d/--2d", help="2D or 3D structure"),
) -> None:
    """Download a chemical structure from PubChem."""
    console.print(
        Panel(
            "[bold yellow]Feature coming in Phase 4[/bold yellow]\nStructure download",
            expand=False,
        )
    )


if __name__ == "__main__":
    app()