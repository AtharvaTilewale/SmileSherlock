"""SmileSherlock: High-performance SMILES validation and PubChem lookup."""

from typing import Optional, Union

from smilesherlock.core.database import DatabaseManager
from smilesherlock.core.pubchem import PubChemClient, PubChemCompound
from smilesherlock.core.smiles import SMILESValidationResult, validate_smiles

__version__ = "1.0.0"
__author__ = "Atharva Tilewale"
__license__ = "MIT"


def lookup(
    query: Union[str, int],
    search_type: str = "auto",
    use_cache: bool = True,
) -> Optional[PubChemCompound]:
    """
    Lookup chemical compound information from PubChem with local caching.

    Args:
        query: SMILES string, PubChem CID, Name, InChI, or InChIKey.
        search_type: 'auto', 'smiles', 'cid', 'name', 'inchi', 'inchikey'.
        use_cache: Whether to use local SQLite database caching.

    Returns:
        PubChemCompound model instance or None.
    """
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


__all__ = [
    "lookup",
    "validate_smiles",
    "SMILESValidationResult",
    "PubChemClient",
    "PubChemCompound",
    "DatabaseManager",
]