"""SmileSherlock: High-performance SMILES validation and PubChem lookup."""

from pathlib import Path
from typing import Optional, Union, List

from smilesherlock.core.database import DatabaseManager
from smilesherlock.core.pubchem import PubChemClient, PubChemCompound
from smilesherlock.core.smiles import SMILESValidationResult, validate_smiles
from smilesherlock.utils.parsers import parse_compounds_file
from smilesherlock.utils.export import export_results

__version__ = "1.0.0"
__author__ = "Atharva Tilewale"
__license__ = "MIT"


def lookup(
    query: Union[str, int],
    search_type: str = "auto",
    use_cache: bool = True,
) -> Optional[PubChemCompound]:
    """Lookup chemical compound information from PubChem with local caching."""
    query_str = str(query).strip()
    db = DatabaseManager()

    if use_cache:
        db.init_db()
        cached = db.get_cached_compound(query_str)
        if cached:
            return cached

    client = PubChemClient()
    compound = client.lookup(query_str, search_type=search_type)

    if compound and use_cache:
        db.cache_compound(query_str, compound)
        if compound.canonical_smiles:
            db.cache_compound(compound.canonical_smiles, compound)
        if compound.cid:
            db.cache_compound(str(compound.cid), compound)

    return compound


def lookup_file(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    output_format: str = "csv",
    remove_duplicates: bool = True,
) -> List[PubChemCompound]:
    """Process a batch file of SMILES/CIDs and export the results."""
    input_path = Path(input_file)
    queries = parse_compounds_file(input_path)
    
    if remove_duplicates:
        queries = list(dict.fromkeys(queries))
        
    results = []
    for query in queries:
        compound = lookup(query)
        if compound:
            results.append(compound)
            
    if output_file:
        export_results(results, Path(output_file), output_format)
        
    return results


def download_structure(
    cid: int,
    format: str = "sdf",
    dimension: str = "3d",
    output_dir: str = "structures",
    force: bool = False,
) -> str:
    """
    Download a chemical structure from PubChem.
    
    Args:
        cid: PubChem Compound ID.
        format: Output format ('sdf', 'mol', 'pdb', 'png').
        dimension: '2d' or '3d'.
        output_dir: Destination folder path.
        force: Overwrite existing files (bypasses resume).
        
    Returns:
        Status message string.
    """
    client = PubChemClient()
    return client.download_structure(cid, format, dimension, output_dir, force)


__all__ = [
    "lookup",
    "lookup_file",
    "download_structure",
    "validate_smiles",
    "SMILESValidationResult",
    "PubChemClient",
    "PubChemCompound",
    "DatabaseManager",
]