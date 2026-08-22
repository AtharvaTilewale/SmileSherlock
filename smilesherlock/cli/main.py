"""SmileSherlock CLI Application."""

from pathlib import Path
from typing import Optional
import re
import hashlib
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from smilesherlock import (
    __version__, lookup, lookup_file, download_structure, generate_structure, validate_smiles,
    compute_fingerprint, apply_filters, compute_similarity,
    FingerprintResult, FilterResult, SimilarityResult,
)
from smilesherlock.config import settings
from smilesherlock.core.pubchem import PubChemCompound
from smilesherlock.utils.parsers import parse_compounds_file
from smilesherlock.utils.export import export_results

app = typer.Typer(
    name="smilesherlock",
    help="SmileSherlock: High-performance SMILES validation, property calculation, and PubChem lookup.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(
            f"[bold blue]SmileSherlock[/bold blue] version [green]{__version__}[/green]\n"
            f"[dim]High-performance SMILES validation and PubChem lookup[/dim]\n"
            f"[dim]License: MIT | Repository: https://github.com/AtharvaTilewale/SmileSherlock[/dim]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """SmileSherlock CLI entry point."""
    pass


@app.command()
def status() -> None:
    """Display system status, cache paths, and configuration."""
    table = Table(title="SmileSherlock Status & Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Configuration", "Loaded")
    table.add_row("Cache Enabled", str(settings.enable_cache))
    table.add_row("Cache Dir", str(settings.cache_dir))
    table.add_row("Database Path", str(settings.db_path))
    table.add_row("Log Dir", str(settings.log_dir))
    table.add_row("Log Level", settings.log_level)
    table.add_row("PubChem Base URL", settings.pubchem_base_url)
    table.add_row("Rate Limit Delay", f"{settings.rate_limit_delay}s")
    table.add_row("Max Workers", str(settings.max_workers))

    console.print(table)


@app.command(name="lookup")
def lookup_cmd(
    query: str = typer.Argument(..., help="SMILES, PubChem CID, InChIKey, or Compound Name"),
    search_type: str = typer.Option("auto", "--type", "-t", help="Search type (auto, cid, smiles, name, inchikey)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass local cache"),
) -> None:
    """Look up compound information by SMILES, CID, InChIKey, or Name."""
    with console.status(f"[bold green]Searching for '{query}'...[/bold green]"):
        compound = lookup(query, search_type=search_type, use_cache=not no_cache)

    if not compound:
        console.print(f"[red]✖ No compound found for query:[/red] [bold]{query}[/bold]")
        raise typer.Exit(code=1)

    table = Table(title=f"Compound Details: {query}", show_header=True, header_style="bold blue")
    table.add_column("Property", style="cyan", width=24)
    table.add_column("Value", style="white")

    if compound.cid:
        table.add_row("PubChem CID", str(compound.cid))
    if compound.iupac_name:
        table.add_row("IUPAC Name", compound.iupac_name)
    if compound.canonical_smiles:
        table.add_row("Canonical SMILES", compound.canonical_smiles)
    if compound.isomeric_smiles and compound.isomeric_smiles != compound.canonical_smiles:
        table.add_row("Isomeric SMILES", compound.isomeric_smiles)
    if compound.molecular_formula:
        table.add_row("Formula", compound.molecular_formula)
    if compound.molecular_weight:
        table.add_row("Molecular Weight", f"{compound.molecular_weight:.4f} g/mol")
    if compound.xlogp is not None:
        table.add_row("XLogP", f"{compound.xlogp:.2f}")
    if compound.hbond_donor_count is not None:
        table.add_row("H-Bond Donors", str(compound.hbond_donor_count))
    if compound.hbond_acceptor_count is not None:
        table.add_row("H-Bond Acceptors", str(compound.hbond_acceptor_count))
    if compound.inchi:
        table.add_row("InChI", compound.inchi)
    if compound.inchikey:
        table.add_row("InChIKey", compound.inchikey)

    console.print(table)


@app.command()
def batch(
    input_file: Path = typer.Argument(..., help="Path to input file (.csv, .tsv, .xlsx, .smi, .sdf)"),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, xlsx, json)"),
    keep_duplicates: bool = typer.Option(False, "--keep-duplicates", help="Do not remove duplicate entries"),
) -> None:
    """Process a batch of SMILES from a file and retrieve metadata."""
    if not input_file.exists():
        console.print(f"[red]✖ Input file not found: {input_file}[/red]")
        raise typer.Exit(code=1)

    if not output_file:
        output_file = input_file.with_name(f"{input_file.stem}_results.{format}")

    report_file = output_file.with_name(f"{output_file.stem}_report.log")

    try:
        queries = parse_compounds_file(input_file)
        original_count = len(queries)

        if not keep_duplicates:
            queries = list(dict.fromkeys(queries))

        console.print(f"[blue]ℹ[/blue] Loaded {original_count} compounds ({len(queries)} unique).")
    except Exception as e:
        console.print(f"[red]✖ Failed to parse input file: {e}[/red]")
        raise typer.Exit(code=1)

    results = []
    log_entries = []
    found_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Looking up compounds...", total=len(queries))

        for query in queries:
            compound = lookup(query, use_cache=True)
            if compound:
                results.append(compound)
                found_count += 1
                log_entries.append(f"[SUCCESS] Query: '{query}' -> Found CID: {compound.cid}")
            else:
                results.append(PubChemCompound(input_query=query))
                log_entries.append(f"[FAILED]  Query: '{query}' -> Reason: Not found in PubChem")

            progress.advance(task)

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(log_entries))

        export_results(results, output_file, format)
        console.print(f"\n[green]✔[/green] Batch processing complete!")
        console.print(f"  • Found: [green]{found_count}[/green]")
        console.print(f"  • Missed: [red]{len(queries) - found_count}[/red]")
        console.print(f"  • Results saved to: [cyan]{output_file}[/cyan]")
        console.print(f"  • Report log saved to: [cyan]{report_file}[/cyan]")
    except Exception as e:
        console.print(f"[red]✖ Failed to export results: {e}[/red]")


def _sanitize_name_for_filename(name: str) -> str:
    """Generate a clean, filesystem-safe filename stem."""
    clean = re.sub(r'[\\/*?:"<>|]', '_', str(name).strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    if not clean:
        clean = "compound"
    if len(clean) > 40:
        short_hash = hashlib.md5(str(name).encode("utf-8")).hexdigest()[:8]
        clean = clean[:30] + "_" + short_hash
    return clean


def _resolve_smiles_for_query(query_str: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Resolve SMILES, CID, and compound title for a query string.
    Returns (smiles, cid, title).
    """
    val = validate_smiles(query_str)
    if val.is_valid and val.canonical_smiles:
        # Query itself is a valid SMILES string
        # Check if CID can also be found in cache/PubChem without failing if not found
        compound = lookup(val.canonical_smiles, use_cache=True)
        cid = compound.cid if compound else None
        title = (compound.iupac_name or val.canonical_smiles) if compound else val.canonical_smiles
        return val.canonical_smiles, cid, title

    # Not directly a SMILES; lookup in PubChem/cache
    compound = lookup(query_str, use_cache=True)
    if compound:
        smi = compound.canonical_smiles or compound.isomeric_smiles
        return smi, compound.cid, compound.iupac_name or query_str

    return None, None, None


@app.command()
def download(
    query: Optional[str] = typer.Argument(None, help="PubChem CID, SMILES, or compound name"),
    input_file: Optional[Path] = typer.Option(None, "--file", "-i", help="Batch download from file (CSVs, TSV, XLSX, SMI, SDF)"),
    format: str = typer.Option("sdf", "--format", "-f", help="Structure format (sdf, mol, pdb, png)"),
    is_3d: bool = typer.Option(True, "--3d/--2d", help="Download/generate 3D structure (use --2d for 2D)"),
    output_dir: Path = typer.Option(Path("structures"), "--output-dir", "-o", help="Output directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files (disables resume)"),
    gen: Optional[str] = typer.Option(
        None,
        "--gen",
        "-g",
        help="Structure generation mode: 'all' (generate all locally from SMILES) or 'missing' (generate only when not in PubChem/database)",
    ),
) -> None:
    """Download chemical structures from PubChem or generate 2D/3D structures locally from SMILES."""
    if not query and not input_file:
        console.print("[red]✖ You must provide either a query (CID/SMILES/Name) or an --file input.[/red]")
        raise typer.Exit(code=1)

    if gen is not None:
        gen = gen.lower().strip()
        if gen not in ["all", "missing"]:
            console.print(f"[red]✖ Invalid value for --gen: '{gen}'. Allowed values are 'all' or 'missing'.[/red]")
            raise typer.Exit(code=1)

    fmt = format.lower().strip()
    dimension = "3d" if is_3d else "2d"

    if gen == "all" and fmt not in ["sdf", "mol", "pdb"]:
        console.print(f"[red]✖ Structure generation does not support format '{format}'. Supported formats: sdf, mol, pdb.[/red]")
        raise typer.Exit(code=1)

    out_dir_str = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. Single Query Handling
    # -------------------------------------------------------------------------
    if query:
        query_str = str(query).strip()

        if gen == "all":
            with console.status(f"[bold green]Generating {dimension.upper()} {fmt.upper()} for '{query_str}'...[/bold green]"):
                smi, cid_val, title = _resolve_smiles_for_query(query_str)
                if smi:
                    stem = str(cid_val) if cid_val else _sanitize_name_for_filename(query_str)
                    out_path = output_dir / f"{stem}_{dimension}.{fmt}"
                    status = generate_structure(smi, out_path, format=fmt, dimension=dimension, force=force, title=title)
                    if status == "Generated":
                        console.print(f"[green]✔[/green] Successfully generated to [cyan]{out_path}[/cyan]")
                    elif "Skipped" in status:
                        console.print(f"[blue]ℹ[/blue] {status}")
                    else:
                        console.print(f"[red]✖[/red] Failed to generate: {status}")
                        raise typer.Exit(code=1)
                else:
                    console.print(f"[red]✖[/red] Could not resolve SMILES for '{query_str}' to generate structure.")
                    raise typer.Exit(code=1)

        elif gen == "missing":
            with console.status(f"[bold green]Downloading/Generating {dimension.upper()} {fmt.upper()} for '{query_str}'...[/bold green]"):
                target_cid = int(query_str) if query_str.isdigit() else None
                compound = None
                if not target_cid:
                    compound = lookup(query_str, use_cache=True)
                    if compound and compound.cid:
                        target_cid = compound.cid

                downloaded = False
                if target_cid:
                    dl_status = download_structure(target_cid, fmt, dimension, out_dir_str, force)
                    if dl_status == "Downloaded":
                        console.print(f"[green]✔[/green] Successfully downloaded to [cyan]{output_dir}/{target_cid}_{dimension}.{fmt}[/cyan]")
                        downloaded = True
                    elif "Skipped" in dl_status:
                        console.print(f"[blue]ℹ[/blue] {dl_status}")
                        downloaded = True

                if not downloaded:
                    # Fallback to local generation from SMILES
                    smi = None
                    title = query_str
                    cid_val = target_cid

                    if compound and (compound.canonical_smiles or compound.isomeric_smiles):
                        smi = compound.canonical_smiles or compound.isomeric_smiles
                        title = compound.iupac_name or query_str
                    else:
                        val = validate_smiles(query_str)
                        if val.is_valid and val.canonical_smiles:
                            smi = val.canonical_smiles

                    if smi and fmt in ["sdf", "mol", "pdb"]:
                        stem = str(cid_val) if cid_val else _sanitize_name_for_filename(query_str)
                        out_path = output_dir / f"{stem}_{dimension}.{fmt}"
                        gen_status = generate_structure(smi, out_path, format=fmt, dimension=dimension, force=force, title=title)
                        if gen_status == "Generated":
                            console.print(f"[green]✔[/green] (PubChem unavailable) Generated structure locally to [cyan]{out_path}[/cyan]")
                        elif "Skipped" in gen_status:
                            console.print(f"[blue]ℹ[/blue] {gen_status}")
                        else:
                            console.print(f"[red]✖[/red] Failed to generate structure: {gen_status}")
                            raise typer.Exit(code=1)
                    else:
                        console.print(f"[red]✖[/red] Structure not found in PubChem/database and could not be generated locally.")
                        raise typer.Exit(code=1)

        else:
            # Default: PubChem download
            with console.status(f"[bold green]Downloading {dimension.upper()} {fmt.upper()} for '{query_str}'...[/bold green]"):
                target_cid = int(query_str) if query_str.isdigit() else None
                if not target_cid:
                    compound = lookup(query_str, use_cache=True)
                    if compound and compound.cid:
                        target_cid = compound.cid

                if target_cid:
                    status = download_structure(target_cid, fmt, dimension, out_dir_str, force)
                    if status == "Downloaded":
                        console.print(f"[green]✔[/green] Successfully downloaded to [cyan]{output_dir}/{target_cid}_{dimension}.{fmt}[/cyan]")
                    elif "Skipped" in status:
                        console.print(f"[blue]ℹ[/blue] {status}")
                    else:
                        console.print(f"[red]✖[/red] Failed to download: {status}")
                        raise typer.Exit(code=1)
                else:
                    console.print(f"[red]✖[/red] Could not resolve PubChem CID for '{query_str}'. Use --gen all or --gen missing to generate from SMILES.")
                    raise typer.Exit(code=1)

    # -------------------------------------------------------------------------
    # 2. Batch Download/Generation from File
    # -------------------------------------------------------------------------
    if input_file:
        if not input_file.exists():
            console.print(f"[red]✖ Input file not found: {input_file}[/red]")
            raise typer.Exit(code=1)

        report_file = output_dir / f"{input_file.stem}_download_report.log"

        try:
            queries = parse_compounds_file(input_file)
            queries = list(dict.fromkeys(queries))
        except Exception as e:
            console.print(f"[red]✖ Failed to parse input file: {e}[/red]")
            raise typer.Exit(code=1)

        action_desc = "generating" if gen == "all" else "downloading/generating" if gen == "missing" else "downloading"
        console.print(f"[blue]ℹ[/blue] Batch {action_desc} structures for {len(queries)} unique compounds...")

        downloaded_count = 0
        generated_count = 0
        skipped_count = 0
        failed_count = 0
        log_entries = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Processing structures...", total=len(queries))

            for q in queries:
                q_str = str(q).strip()

                if gen == "all":
                    smi, cid_val, title = _resolve_smiles_for_query(q_str)
                    if smi:
                        stem = str(cid_val) if cid_val else _sanitize_name_for_filename(q_str)
                        out_path = output_dir / f"{stem}_{dimension}.{fmt}"
                        status = generate_structure(smi, out_path, format=fmt, dimension=dimension, force=force, title=title)
                        if status == "Generated":
                            generated_count += 1
                            log_entries.append(f"[GENERATED] Query: '{q_str}' -> Saved to {out_path.name}")
                        elif "Skipped" in status:
                            skipped_count += 1
                            log_entries.append(f"[SKIPPED]   Query: '{q_str}' -> Reason: {status}")
                        else:
                            failed_count += 1
                            log_entries.append(f"[FAILED]    Query: '{q_str}' -> Reason: {status}")
                    else:
                        failed_count += 1
                        log_entries.append(f"[FAILED]    Query: '{q_str}' -> Reason: Could not resolve SMILES")

                elif gen == "missing":
                    target_cid = int(q_str) if q_str.isdigit() else None
                    compound = None
                    if not target_cid:
                        compound = lookup(q_str, use_cache=True)
                        if compound and compound.cid:
                            target_cid = compound.cid

                    handled = False
                    if target_cid:
                        dl_status = download_structure(target_cid, fmt, dimension, out_dir_str, force)
                        if dl_status == "Downloaded":
                            downloaded_count += 1
                            log_entries.append(f"[DOWNLOADED] Query: '{q_str}' -> CID {target_cid} -> Saved from PubChem")
                            handled = True
                        elif "Skipped" in dl_status:
                            skipped_count += 1
                            log_entries.append(f"[SKIPPED]    Query: '{q_str}' -> CID {target_cid} -> Reason: {dl_status}")
                            handled = True

                    if not handled:
                        # Fall back to generate locally from SMILES
                        smi = None
                        title = q_str
                        cid_val = target_cid
                        if compound and (compound.canonical_smiles or compound.isomeric_smiles):
                            smi = compound.canonical_smiles or compound.isomeric_smiles
                            title = compound.iupac_name or q_str
                        else:
                            val = validate_smiles(q_str)
                            if val.is_valid and val.canonical_smiles:
                                smi = val.canonical_smiles

                        if smi and fmt in ["sdf", "mol", "pdb"]:
                            stem = str(cid_val) if cid_val else _sanitize_name_for_filename(q_str)
                            out_path = output_dir / f"{stem}_{dimension}.{fmt}"
                            gen_status = generate_structure(smi, out_path, format=fmt, dimension=dimension, force=force, title=title)
                            if gen_status == "Generated":
                                generated_count += 1
                                log_entries.append(f"[GENERATED]  Query: '{q_str}' -> (PubChem unavailable) Generated locally to {out_path.name}")
                            elif "Skipped" in gen_status:
                                skipped_count += 1
                                log_entries.append(f"[SKIPPED]    Query: '{q_str}' -> Reason: {gen_status}")
                            else:
                                failed_count += 1
                                log_entries.append(f"[FAILED]     Query: '{q_str}' -> Reason: {gen_status}")
                        else:
                            failed_count += 1
                            log_entries.append(f"[FAILED]     Query: '{q_str}' -> Reason: Not available in PubChem and cannot generate")

                else:
                    # Default: PubChem download only
                    target_cid = int(q_str) if q_str.isdigit() else None
                    if not target_cid:
                        compound = lookup(q_str, use_cache=True)
                        if compound and compound.cid:
                            target_cid = compound.cid

                    if target_cid:
                        status = download_structure(target_cid, fmt, dimension, out_dir_str, force)
                        if status == "Downloaded":
                            downloaded_count += 1
                            log_entries.append(f"[DOWNLOADED] Query: '{q_str}' -> CID {target_cid} -> Downloaded")
                        elif "Skipped" in status:
                            skipped_count += 1
                            log_entries.append(f"[SKIPPED]    Query: '{q_str}' -> Reason: {status}")
                        else:
                            failed_count += 1
                            log_entries.append(f"[FAILED]     Query: '{q_str}' -> Reason: {status}")
                    else:
                        failed_count += 1
                        log_entries.append(f"[FAILED]     Query: '{q_str}' -> Reason: Could not resolve PubChem CID")

                progress.advance(task)

        # Save status log
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(log_entries))

        console.print(f"\n[green]✔[/green] Batch processing complete!")
        if gen in ["all", "missing"]:
            console.print(f"    Downloaded: [green]{downloaded_count}[/green]")
            console.print(f"    Generated:  [green]{generated_count}[/green]")
        else:
            console.print(f"    Downloaded: [green]{downloaded_count}[/green]")
        console.print(f"    Skipped (Already exist): [blue]{skipped_count}[/blue]")
        console.print(f"    Failed/Not Found:        [red]{failed_count}[/red]")
        console.print(f"    Saved in: [cyan]{output_dir}[/cyan]")
        console.print(f"    Report log saved to: [cyan]{report_file}[/cyan]")



# ═══════════════════════════════════════════════════════════════════════════════
# fingerprint command
# ═══════════════════════════════════════════════════════════════════════════════

@app.command(name="fingerprint")
def fingerprint_cmd(
    smiles: str = typer.Argument(None, help="SMILES string of the compound to fingerprint"),
    file: Optional[Path] = typer.Option(None, "--file", "-i", help="Input file (.csv, .smi, .txt) for batch processing"),
    fp_type: str = typer.Option("ecfp4", "--type", "-t", help="Fingerprint type: ecfp4, ecfp6, fcfp4, maccs, rdkit, atompair, torsion, all"),
    bits: int = typer.Option(2048, "--bits", "-b", help="Number of bits (ignored for MACCS which is fixed at 167)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output CSV file for batch results"),
) -> None:
    """Generate molecular fingerprints from SMILES (offline, RDKit-based).

    Supports ECFP4, ECFP6, FCFP4, MACCS, RDKit, AtomPair, and Topological Torsion fingerprints.
    """
    if smiles is None and file is None:
        console.print("[red]Error:[/red] Provide a SMILES argument or --file for batch input.")
        raise typer.Exit(code=1)

    valid_types = {"ecfp4", "ecfp6", "fcfp4", "maccs", "rdkit", "atompair", "torsion", "all"}
    if fp_type.lower() not in valid_types:
        console.print(f"[red]Error:[/red] Unknown fingerprint type '{fp_type}'. Valid: {sorted(valid_types)}")
        raise typer.Exit(code=1)

    # ── Single SMILES mode ──────────────────────────────────────────────────
    if smiles is not None and file is None:
        try:
            result = compute_fingerprint(smiles, fp_type=fp_type, n_bits=bits)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

        results = result if isinstance(result, list) else [result]

        table = Table(
            title=f"[bold]Fingerprint Results[/bold] — {smiles[:60]}{'...' if len(smiles) > 60 else ''}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Type", style="cyan", min_width=12)
        table.add_column("Bits", justify="right", style="white")
        table.add_column("On Bits", justify="right", style="green")
        table.add_column("Density", justify="right", style="yellow")
        table.add_column("Bit String (preview)", style="dim")

        for r in results:
            preview = r.bit_string[:64] + "..." if len(r.bit_string) > 64 else r.bit_string
            table.add_row(
                r.fingerprint_type.upper(),
                str(r.n_bits),
                str(r.n_on_bits),
                f"{r.density:.4f}",
                preview,
            )
        console.print(table)
        if len(results) == 1:
            console.print(f"\n[dim]Full bit string ({results[0].n_bits} bits):[/dim]")
            console.print(f"[white]{results[0].bit_string}[/white]")
        return

    # ── Batch file mode ─────────────────────────────────────────────────────
    from smilesherlock.utils.parsers import parse_compounds_file
    queries = parse_compounds_file(file)

    rows = []
    errors = 0
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task("[green]Computing fingerprints...", total=len(queries))
        for q in queries:
            try:
                res = compute_fingerprint(q.strip(), fp_type=fp_type, n_bits=bits)
                res_list = res if isinstance(res, list) else [res]
                for r in res_list:
                    rows.append({
                        "smiles": r.smiles,
                        "fp_type": r.fingerprint_type,
                        "n_bits": r.n_bits,
                        "n_on_bits": r.n_on_bits,
                        "density": r.density,
                        "bit_string": r.bit_string,
                        "hex_string": r.hex_string,
                    })
            except Exception:
                errors += 1
            progress.advance(task)

    if output:
        import csv
        output.parent.mkdir(parents=True, exist_ok=True)
        if rows:
            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        console.print(f"\n[green]Fingerprints saved to[/green]: [cyan]{output}[/cyan]")
    else:
        table = Table(show_header=True, header_style="bold magenta", title="Batch Fingerprint Results")
        table.add_column("SMILES", style="cyan", max_width=30, overflow="fold")
        table.add_column("Type", style="white")
        table.add_column("Bits", justify="right")
        table.add_column("On Bits", justify="right", style="green")
        table.add_column("Density", justify="right", style="yellow")
        for row in rows[:50]:
            table.add_row(row["smiles"][:28], row["fp_type"].upper(), str(row["n_bits"]), str(row["n_on_bits"]), f"{row['density']:.4f}")
        console.print(table)

    console.print(f"\n[green]Done.[/green] Processed: [white]{len(queries)}[/white] | Errors: [red]{errors}[/red]")


# ═══════════════════════════════════════════════════════════════════════════════
# similar command
# ═══════════════════════════════════════════════════════════════════════════════

@app.command(name="similar")
def similar_cmd(
    query: str = typer.Argument(..., help="Query SMILES string to search for"),
    file: Optional[Path] = typer.Option(None, "--file", "-i", help="Library file (.csv, .smi, .txt) to search against"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Minimum Tanimoto similarity (0.0-1.0)"),
    top: int = typer.Option(10, "--top", "-n", help="Number of top results to return"),
    fp_type: str = typer.Option("ecfp4", "--fp-type", help="Fingerprint type: ecfp4, ecfp6, fcfp4, maccs, rdkit, atompair, torsion"),
    bits: int = typer.Option(2048, "--bits", "-b", help="Number of fingerprint bits"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to CSV file"),
) -> None:
    """Search a library file for compounds similar to a query SMILES (Tanimoto similarity).

    Ranks library compounds by Tanimoto similarity. Uses RDKit fingerprints offline.
    """
    if file is None:
        console.print("[red]Error:[/red] --file / -i is required for similarity search.")
        raise typer.Exit(code=1)

    valid_types = {"ecfp4", "ecfp6", "fcfp4", "maccs", "rdkit", "atompair", "torsion"}
    if fp_type.lower() not in valid_types:
        console.print(f"[red]Error:[/red] Unknown fp-type '{fp_type}'. Valid: {sorted(valid_types)}")
        raise typer.Exit(code=1)

    from smilesherlock.utils.parsers import parse_compounds_file
    library = parse_compounds_file(file)

    with console.status(f"[bold green]Searching {len(library)} library compounds...[/bold green]"):
        try:
            hits = compute_similarity(
                query,
                library,
                fp_type=fp_type.lower(),
                n_bits=bits,
                threshold=threshold,
                top_n=top,
            )
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

    if not hits:
        console.print(f"[yellow]No compounds found with Tanimoto similarity >= {threshold}[/yellow]")
        raise typer.Exit()

    table = Table(
        title=f"[bold]Similarity Search Results[/bold] — Top {len(hits)} hits (threshold={threshold}, fp={fp_type.upper()})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Rank", justify="right", style="dim", width=5)
    table.add_column("Similarity", justify="right", style="bold green", width=12)
    table.add_column("Hit SMILES", style="cyan")

    for hit in hits:
        sim_bar = "#" * int(hit.similarity * 10) + "-" * (10 - int(hit.similarity * 10))
        table.add_row(str(hit.rank), f"{hit.similarity:.4f} {sim_bar}", hit.hit)

    console.print(table)
    console.print(f"\n[dim]Query:[/dim] [white]{query}[/white]")
    console.print(f"[dim]Library:[/dim] [white]{file}[/white] ({len(library)} compounds)")
    console.print(f"[dim]Fingerprint:[/dim] [white]{fp_type.upper()}, {bits} bits[/white]")

    if output:
        import csv
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["rank", "query", "hit", "similarity", "fingerprint_type"])
            writer.writeheader()
            for h in hits:
                writer.writerow(h.model_dump())
        console.print(f"\n[green]Results saved to[/green]: [cyan]{output}[/cyan]")


# ═══════════════════════════════════════════════════════════════════════════════
# filter command
# ═══════════════════════════════════════════════════════════════════════════════

@app.command(name="filter")
def filter_cmd(
    smiles: str = typer.Argument(None, help="Single SMILES string to evaluate"),
    file: Optional[Path] = typer.Option(None, "--file", "-i", help="Input file for batch evaluation"),
    rules: str = typer.Option("all", "--rules", "-r", help="Comma-separated rules: lipinski,veber,ghose,egan,ro3,pains,qed or all"),
    fail: bool = typer.Option(False, "--fail", help="Invert output: keep only compounds that FAIL the filter (useful for PAINS removal)"),
    qed_min: float = typer.Option(0.0, "--qed-min", help="Minimum QED score to keep (0.0-1.0)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to CSV file"),
) -> None:
    """Apply drug-likeness and ADMET filters to SMILES compounds (offline, RDKit-based).

    Evaluates: Lipinski Ro5, Veber, Ghose, Egan, Ro3, PAINS alerts, and QED score.
    """
    if smiles is None and file is None:
        console.print("[red]Error:[/red] Provide a SMILES argument or --file for batch input.")
        raise typer.Exit(code=1)

    # Parse rules list
    rule_list = [r.strip().lower() for r in rules.split(",")]

    # ── Single SMILES mode ──────────────────────────────────────────────────
    if smiles is not None and file is None:
        try:
            result = apply_filters(smiles, rules=rule_list)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

        if result.error:
            console.print(f"[red]Error:[/red] {result.error}")
            raise typer.Exit(code=1)

        # Properties table
        prop_table = Table(title="[bold]Physicochemical Properties[/bold]", show_header=True, header_style="bold blue")
        prop_table.add_column("Property", style="cyan")
        prop_table.add_column("Value", justify="right", style="white")
        prop_table.add_column("Property", style="cyan")
        prop_table.add_column("Value", justify="right", style="white")

        prop_table.add_row(
            "Mol Weight (g/mol)", f"{result.molecular_weight:.3f}",
            "LogP (MolLogP)", f"{result.logp:.3f}",
        )
        prop_table.add_row(
            "H-Bond Donors", str(result.hbd),
            "H-Bond Acceptors", str(result.hba),
        )
        prop_table.add_row(
            "TPSA (A^2)", f"{result.tpsa:.3f}",
            "Rotatable Bonds", str(result.rotatable_bonds),
        )
        prop_table.add_row(
            "Heavy Atoms", str(result.heavy_atom_count),
            "Molar Refractivity", f"{result.molar_refractivity:.3f}",
        )
        prop_table.add_row(
            "QED Score", f"[{'green' if result.qed_score >= 0.5 else 'yellow'}]{result.qed_score:.4f}[/{'green' if result.qed_score >= 0.5 else 'yellow'}]",
            "", "",
        )
        console.print(prop_table)

        # Filter results table
        filt_table = Table(title="[bold]Filter Results[/bold]", show_header=True, header_style="bold magenta")
        filt_table.add_column("Rule", style="cyan", min_width=18)
        filt_table.add_column("Result", width=10)
        filt_table.add_column("Details", style="dim")

        rule_map = {
            "lipinski": ("Lipinski Ro5", result.lipinski),
            "veber": ("Veber", result.veber),
            "ghose": ("Ghose", result.ghose),
            "egan": ("Egan", result.egan),
            "ro3": ("Ro3 (Lead-like)", result.ro3),
            "pains": ("PAINS", result.pains),
        }
        for key, (label, rule_result) in rule_map.items():
            if rule_result is not None:
                icon = "[green]PASS[/green]" if rule_result.passed else "[red]FAIL[/red]"
                filt_table.add_row(label, icon, rule_result.details)

        overall = "[green]PASS[/green]" if result.passes_all else "[red]FAIL[/red]"
        filt_table.add_row("[bold]Overall[/bold]", overall, "All requested rules")
        console.print(filt_table)
        return

    # ── Batch file mode ─────────────────────────────────────────────────────
    import csv
    from smilesherlock.utils.parsers import parse_compounds_file
    queries = parse_compounds_file(file)

    rows = []
    pass_count = 0
    fail_count = 0
    error_count = 0

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TaskProgressColumn(), console=console) as progress:
        task = progress.add_task("[green]Applying filters...", total=len(queries))
        for q in queries:
            try:
                r = apply_filters(q.strip(), rules=rule_list)
                if r.error:
                    error_count += 1
                    progress.advance(task)
                    continue

                # Apply QED threshold
                if qed_min > 0 and (r.qed_score is None or r.qed_score < qed_min):
                    progress.advance(task)
                    continue

                is_kept = (r.passes_all and not fail) or (not r.passes_all and fail)
                if is_kept:
                    row = {
                        "smiles": r.smiles,
                        "mw": r.molecular_weight,
                        "logp": r.logp,
                        "hbd": r.hbd,
                        "hba": r.hba,
                        "tpsa": r.tpsa,
                        "rotatable_bonds": r.rotatable_bonds,
                        "heavy_atoms": r.heavy_atom_count,
                        "qed": r.qed_score,
                        "lipinski": r.lipinski.passed if r.lipinski else "",
                        "veber": r.veber.passed if r.veber else "",
                        "ghose": r.ghose.passed if r.ghose else "",
                        "egan": r.egan.passed if r.egan else "",
                        "ro3": r.ro3.passed if r.ro3 else "",
                        "pains_clean": r.pains.passed if r.pains else "",
                        "passes_all": r.passes_all,
                    }
                    rows.append(row)

                if r.passes_all:
                    pass_count += 1
                else:
                    fail_count += 1
            except Exception:
                error_count += 1
            progress.advance(task)

    # Show summary table (first 20)
    summary_table = Table(show_header=True, header_style="bold magenta",
                          title=f"[bold]Filter Results — {'Failures' if fail else 'Passes'} ({len(rows)} compounds)[/bold]")
    summary_table.add_column("SMILES", style="cyan", max_width=30, overflow="fold")
    summary_table.add_column("MW", justify="right")
    summary_table.add_column("LogP", justify="right")
    summary_table.add_column("QED", justify="right")
    summary_table.add_column("Overall", justify="center")

    for row in rows[:20]:
        overall_str = "[green]PASS[/green]" if row["passes_all"] else "[red]FAIL[/red]"
        summary_table.add_row(
            row["smiles"][:28],
            str(row["mw"]),
            str(row["logp"]),
            str(row["qed"]),
            overall_str,
        )
    console.print(summary_table)

    console.print(f"\n[bold]Summary[/bold]: Total={len(queries)} | Pass={pass_count} | Fail={fail_count} | Errors={error_count}")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        if rows:
            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        console.print(f"[green]Results saved to[/green]: [cyan]{output}[/cyan]")


if __name__ == "__main__":
    app()
