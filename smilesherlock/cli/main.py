"""Main CLI application for SmileSherlock."""

from pathlib import Path
from typing import Optional
import concurrent.futures
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from smilesherlock import __version__, lookup, lookup_file, validate_smiles, download_structure
from smilesherlock.config import settings
from smilesherlock.core.database import DatabaseManager
from smilesherlock.utils.parsers import parse_compounds_file
from smilesherlock.logging_config import logger

app = typer.Typer(
    name="smilesherlock",
    help="High-performance SMILES validation and PubChem lookup",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
) -> None:
    if version:
        console.print(Panel(f"[bold cyan]SmileSherlock[/bold cyan] v{__version__}", expand=False))
        raise typer.Exit()


@app.command()
def status() -> None:
    """Show current configuration and system status."""
    console.print(Panel("[bold cyan]SmileSherlock Status[/bold cyan]", expand=False))
    config_table = Table(title="Configuration", show_header=True)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Cache Dir", str(settings.cache_dir))
    config_table.add_row("Database", str(settings.db_path))
    config_table.add_row("PubChem URL", settings.pubchem_base_url)
    config_table.add_row("Max Workers (Threads)", str(settings.max_workers))
    console.print(config_table)


@app.command()
def init() -> None:
    """Initialize SmileSherlock directories and SQLite database schema."""
    console.print(Panel("[bold cyan]Initializing SmileSherlock[/bold cyan]", expand=False))
    try:
        db_mgr = DatabaseManager()
        db_mgr.init_db()
        console.print(f"[green]✔[/green] Database schema initialized at {settings.db_path}")
        console.print("\n[green bold]✨ Initialization complete![/green bold]")
    except Exception as e:
        console.print(f"[red]✖ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command(name="lookup")
def lookup_cmd(
    query: str = typer.Argument(..., help="SMILES string, CID, Name, InChI, or InChIKey"),
    cid: bool = typer.Option(False, "--cid", help="Treat input explicitly as PubChem CID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output result in JSON format"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable database caching"),
) -> None:
    """Lookup a single compound in PubChem."""
    search_type = "cid" if cid else "auto"

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
    console.print(table)


@app.command()
def batch(
    input_file: Path = typer.Argument(..., help="Input file (CSV, TSV, XLSX, SMI, SDF)"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, xlsx, json)"),
    keep_duplicates: bool = typer.Option(False, "--keep-duplicates", help="Do not remove duplicate entries"),
) -> None:
    """Process a batch of SMILES from a file utilizing Threading."""
    if not input_file.exists():
        console.print(f"[red]✖ Input file not found: {input_file}[/red]")
        raise typer.Exit(code=1)

    if not output_file:
        output_file = input_file.with_name(f"{input_file.stem}_results.{format}")

    queries = parse_compounds_file(input_file)
    if not keep_duplicates:
        queries = list(dict.fromkeys(queries))
        
    console.print(f"[blue]ℹ[/blue] Multithreading ({settings.max_workers} workers) batch process for {len(queries)} unique compounds.")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching from PubChem...", total=len(queries))
        
        # Pass progress.advance as a callback to the threaded lookup_file function
        results = lookup_file(
            input_file=input_file,
            output_file=output_file,
            output_format=format,
            remove_duplicates=not keep_duplicates,
            progress_callback=lambda: progress.advance(task)
        )

    found = sum(1 for r in results if r.cid is not None)
    console.print(f"\n[green]✔[/green] Batch processing complete!")
    console.print(f"  • Found: [green]{found}[/green] | Missed: [red]{len(results) - found}[/red]")
    console.print(f"  • Results saved to: [cyan]{output_file}[/cyan]")


@app.command()
def download(
    cid: Optional[int] = typer.Argument(None, help="PubChem CID to download"),
    input_file: Optional[Path] = typer.Option(None, "--file", "-i", help="Batch download from file"),
    format: str = typer.Option("sdf", "--format", "-f", help="Structure format (sdf, mol, pdb, png)"),
    dimension: str = typer.Option("3d", "--3d/--2d", help="2D or 3D structure"),
    output_dir: Path = typer.Option(Path("structures"), "--output-dir", "-o", help="Output directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
) -> None:
    """Download chemical structures from PubChem with Threading."""
    if not cid and not input_file:
        console.print("[red]✖ You must provide either a CID or an --file input.[/red]")
        raise typer.Exit(code=1)

    out_dir_str = str(output_dir)

    # Single Download
    if cid:
        with console.status(f"[bold green]Downloading {dimension.upper()} {format.upper()} for CID {cid}...[/bold green]"):
            status = download_structure(cid, format, dimension, out_dir_str, force)
            if status == "Downloaded":
                console.print(f"[green]✔[/green] Successfully downloaded to {output_dir}/{cid}_{dimension.lower()}.{format.lower()}")
            elif "Skipped" in status:
                console.print(f"[blue]ℹ[/blue] {status}")
            else:
                console.print(f"[red]✖[/red] Failed to download: {status}")
    
    # Threaded Batch Download
    if input_file:
        queries = parse_compounds_file(input_file)
        queries = list(dict.fromkeys(queries)) 
        console.print(f"[blue]ℹ[/blue] Multithreading ({settings.max_workers} workers) batch download for {len(queries)} structures...")
        
        success, skipped, failed = 0, 0, 0
        
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing downloads...", total=len(queries))
            
            def process_download(query):
                target_cid = int(query) if str(query).isdigit() else getattr(lookup(query, use_cache=True), 'cid', None)
                if target_cid:
                    return download_structure(target_cid, format, dimension, out_dir_str, force)
                return "Not Found"

            with concurrent.futures.ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                future_to_query = {executor.submit(process_download, q): q for q in queries}
                for future in concurrent.futures.as_completed(future_to_query):
                    status = future.result()
                    if status == "Downloaded": success += 1
                    elif "Skipped" in status: skipped += 1
                    else: failed += 1
                    progress.advance(task)
                
        console.print(f"\n[green]✔[/green] Batch download complete!")
        console.print(f"  • Downloaded: [green]{success}[/green] | Skipped: [blue]{skipped}[/blue] | Failed: [red]{failed}[/red]")
        console.print(f"  • Saved in: [cyan]{output_dir}[/cyan]")

if __name__ == "__main__":
    app()