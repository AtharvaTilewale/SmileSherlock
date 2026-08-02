"""
SmileSherlock: High-performance SMILES validation and PubChem lookup.

A production-grade cheminformatics tool for:
- SMILES validation and canonicalization
- PubChem lookups by SMILES, CID, InChI, name, etc.
- Chemical structure downloads (2D/3D SDF, MOL, PDB, PNG)
- Batch processing with async downloads and caching
- Multiple export formats (CSV, Excel, JSON)
"""

__version__ = "0.1.0"
__author__ = "SmileSherlock Contributors"
__license__ = "MIT"

# Public API (populated in later phases)
__all__ = [
    "lookup",
    "lookup_file",
    "download_structure",
]
