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


from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from smilesherlock.utils.parsers import parse_compounds_file
from smilesherlock.utils.export import export_results

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
    keep_duplicates: bool = typer.Option(False, "--keep-duplicates", help="Do not remove duplicate entries"),
) -> None:
    """
    Process a batch of SMILES from a file and retrieve metadata.
    """
    if not input_file.exists():
        console.print(f"[red]✖ Input file not found: {input_file}[/red]")
        raise typer.Exit(code=1)

    # Determine default output if not provided
    if not output_file:
        output_file = input_file.with_name(f"{input_file.stem}_results.{format}")

    try:
        queries = parse_compounds_file(input_file)
        original_count = len(queries)
        
        if not keep_duplicates:
            # Preserve order while removing duplicates
            queries = list(dict.fromkeys(queries))
            
        console.print(f"[blue]ℹ[/blue] Loaded {original_count} compounds ({len(queries)} unique).")
    except Exception as e:
        console.print(f"[red]✖ Failed to parse input file: {e}[/red]")
        raise typer.Exit(code=1)

    results = []
    found_count = 0

    # Rich progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Looking up compounds...", total=len(queries))

        for query in queries:
            # We call the lookup function we updated in Phase 2
            compound = lookup(query, use_cache=True)
            if compound:
                results.append(compound)
                found_count += 1
            else:
                # If not found, append a blank record with the input query so it isn't lost
                from smilesherlock.core.pubchem import PubChemCompound
                results.append(PubChemCompound(input_query=query))
                
            progress.advance(task)

    try:
        export_results(results, output_file, format)
        console.print(f"\n[green]✔[/green] Batch processing complete!")
        console.print(f"  • Found: [green]{found_count}[/green]")
        console.print(f"  • Missed: [red]{len(queries) - found_count}[/red]")
        console.print(f"  • Results saved to: [cyan]{output_file}[/cyan]")
    except Exception as e:
        console.print(f"[red]✖ Failed to export results: {e}[/red]")


@app.command()
def download(
    cid: Optional[int] = typer.Argument(None, help="PubChem CID to download"),
    input_file: Optional[Path] = typer.Option(None, "--file", "-i", help="Batch download from file (CSVs, SMI, etc.)"),
    format: str = typer.Option("sdf", "--format", "-f", help="Structure format (sdf, mol, pdb, png)"),
    dimension: str = typer.Option("3d", "--3d/--2d", help="2D or 3D structure"),
    output_dir: Path = typer.Option(Path("structures"), "--output-dir", "-o", help="Output directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files (disables resume)"),
) -> None:
    """Download chemical structures from PubChem (Single or Batch)."""
    if not cid and not input_file:
        console.print("[red]✖ You must provide either a CID or an --file input.[/red]")
        raise typer.Exit(code=1)

    from smilesherlock import download_structure, lookup
    from smilesherlock.utils.parsers import parse_compounds_file
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    out_dir_str = str(output_dir)

    # 1. Single CID Download
    if cid:
        with console.status(f"[bold green]Downloading {dimension.upper()} {format.upper()} for CID {cid}...[/bold green]"):
            status = download_structure(cid, format, dimension, out_dir_str, force)
            if status == "Downloaded":
                console.print(f"[green]✔[/green] Successfully downloaded to {output_dir}/{cid}_{dimension.lower()}.{format.lower()}")
            elif "Skipped" in status:
                console.print(f"[blue]ℹ[/blue] {status}")
            else:
                console.print(f"[red]✖[/red] Failed to download: {status}")
    
    # 2. Batch Download from File
    if input_file:
        if not input_file.exists():
            console.print(f"[red]✖ Input file not found: {input_file}[/red]")
            raise typer.Exit(code=1)
        
        queries = parse_compounds_file(input_file)
        queries = list(dict.fromkeys(queries))  # Remove duplicates
        
        console.print(f"[blue]ℹ[/blue] Batch downloading structures for {len(queries)} unique compounds...")
        
        success = 0
        skipped = 0
        failed = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing downloads...", total=len(queries))
            
            for query in queries:
                # Ensure we have a CID (translating SMILES on the fly if needed)
                target_cid = None
                if str(query).isdigit():
                    target_cid = int(query)
                else:
                    compound = lookup(query, use_cache=True)
                    if compound and compound.cid:
                        target_cid = compound.cid
                
                if target_cid:
                    status = download_structure(target_cid, format, dimension, out_dir_str, force)
                    if status == "Downloaded":
                        success += 1
                    elif "Skipped" in status:
                        skipped += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    
                progress.advance(task)
                
        console.print(f"\n[green]✔[/green] Batch download complete!")
        console.print(f"  • Downloaded: [green]{success}[/green]")
        console.print(f"  • Skipped (Already exist): [blue]{skipped}[/blue]")
        console.print(f"  • Failed/Not Found: [red]{failed}[/red]")
        console.print(f"  • Saved in: [cyan]{output_dir}[/cyan]")


if __name__ == "__main__":
    app()