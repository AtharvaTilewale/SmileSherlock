# SmileSherlock

<p align="center">
  <img src="https://raw.githubusercontent.com/AtharvaTilewale/SmileSherlock/main/docs/assets/smilesherlock-logo.png" alt="SmileSherlock logo" width="700" />
</p>

A high-performance, production-grade tool for SMILES validation, PubChem lookup, and chemical structure retrieval.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21763825.svg)](https://doi.org/10.5281/zenodo.21763825)
[![PyPI](https://img.shields.io/pypi/v/smilesherlock)](https://pypi.org/project/smilesherlock/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **SMILES Validation & Canonicalization** - Validate and standardize SMILES strings using RDKit
- **Multi-format Input** - Support for CSV, TSV, XLSX, SMI, SDF, and TXT files
- **Smart Auto-detection** - Automatically identify SMILES columns
- **PubChem Lookup** - Search by SMILES, CID, Name, InChI, and InChIKey
- **Rich Metadata** - Retrieve IUPAC name, molecular formula, mass, descriptors
- **Structure Downloads** - Get 2D/3D SDF, MOL, PDB, and PNG formats from PubChem
- **Offline Molecule Generation (--gen)** - Generate 2D and 3D conformations (SDF, MOL, PDB) offline from SMILES via RDKit with forcefield optimization
- **Molecular Fingerprints** - ECFP4, ECFP6, FCFP4, MACCS, RDKit, AtomPair, Torsion fingerprints offline (`fingerprint` command)
- **Similarity Search** - Tanimoto-based library search with threshold and top-N ranking (`similar` command)
- **Drug-Likeness Filtering** - Lipinski Ro5, Veber, Ghose, Egan, Ro3, PAINS alerts, and QED scoring (`filter` command)
- **Batch Processing** - Process hundreds of compounds with progress tracking
- **Async/Multithreading** - Fast parallel downloads with retry logic
- **Caching** - SQLite database for storing results locally
- **Multiple Exports** - Save results as CSV, Excel, or JSON
- **Python API** - Use directly in your scripts via smilesherlock module
- **CLI Tool** - Full-featured command-line interface with smilesherlock command

## Installation

### From PyPI 

```bash
pip install smilesherlock
```

### Development Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/AtharvaTilewale/SmileSherlock.git
cd SmileSherlock
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Show configuration and status
smilesherlock status

# Initialize directories and database
smilesherlock init

# Lookup a single compound (by SMILES, CID, or Chemical Name)
smilesherlock lookup "c1ccccc1"  # Benzene
smilesherlock lookup "aspirin"
smilesherlock lookup 5282253 --type cid

# Batch process a file to retrieve metadata
smilesherlock batch compounds.csv --output results.xlsx --format xlsx

# Download structure from PubChem
smilesherlock download 5282253 --format sdf --3d

# Generate 3D structure offline from SMILES using RDKit (--gen all)
smilesherlock download "CC(=O)OC1=CC=CC=C1C(=O)O" --gen all --3d --format sdf

# Generate 2D MOL structure locally from SMILES
smilesherlock download "c1ccccc1" --gen all --2d --format mol

# Batch download with offline fallback for missing structures (--gen missing)
smilesherlock download --file compounds.csv --gen missing --3d --format sdf --output-dir ./structures/

# Batch generate all structures offline from a SMILES file (--gen all)
smilesherlock download --file compounds.smi --gen all --3d --format pdb --output-dir ./3d_models/
```

#
### Molecular Fingerprints

```bash
# Generate ECFP4 fingerprint (single compound)
smilesherlock fingerprint "CC(=O)OC1=CC=CC=C1C(=O)O" --type ecfp4

# All 7 fingerprint types at once
smilesherlock fingerprint "CC(=O)OC1=CC=CC=C1C(=O)O" --type all

# Batch - save to CSV
smilesherlock fingerprint --file compounds.smi --type maccs --output fingerprints.csv
```

### Similarity Search

```bash
# Top-10 most similar compounds (Tanimoto >= 0.5)
smilesherlock similar "CC(=O)OC1=CC=CC=C1C(=O)O" --file library.smi --threshold 0.5 --top 10

# Save hits to CSV
smilesherlock similar "CCO" --file compounds.csv --fp-type ecfp6 --output hits.csv
```

### Drug-Likeness Filtering

```bash
# Single compound - all rules
smilesherlock filter "CC(=O)OC1=CC=CC=C1C(=O)O"

# Batch - keep only Lipinski-compliant, PAINS-free compounds
smilesherlock filter --file compounds.csv --rules lipinski,veber,pains --output drug_like.csv

# Remove PAINS compounds from a library
smilesherlock filter --file library.csv --rules pains --output no_pains.csv

# Lead-like compounds with minimum QED 0.5
smilesherlock filter --file library.csv --rules ro3 --qed-min 0.5 --output leads.csv
```

## Python API

```python
from smilesherlock import lookup, lookup_file, download_structure, generate_structure, validate_smiles

# Lookup single compound
result = lookup("c1ccccc1")
print(result.cid, result.iupac_name)

# Process batch file
results = lookup_file("compounds.csv", output_format="xlsx")

# Download structure from PubChem
download_structure(5282253, format="sdf", dimension="3d")

# Generate 2D or 3D structure offline from SMILES
generate_structure(
    smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
    output_path="aspirin_3d.sdf",
    format="sdf",
    dimension="3d",
    title="Aspirin"
)
``` 
For more detailed API documentation, see the **[API Reference](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/docs/api_reference.md)** page.

## Documentation

For complete tutorials and advanced usage examples, see the **[Practical Guide](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/docs/practical_guide.md)** or visit the **[official documentation](https://smilesherlock.readthedocs.io/)** on Read the Docs.

## Requirements

- Python 3.10+
- RDKit (cheminformatics library)
- pandas (data handling)
- requests/aiohttp (HTTP)
- typer (CLI framework)
- rich/tqdm (UI/progress)

## Configuration

For configuration and architecture details, see the **[Configuration & Architecture](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/docs/configuration.md)** page.


## Standardization Pipeline

Clean up "dirty" SMILES: strip salts, neutralize charges, canonicalize tautomers.
Fully **offline** — powered by RDKit `MolStandardize`.

```bash
# Strip salt, neutralize, and canonicalize in one go
smilesherlock standardize "[Na+].[OH-].CC(=O)[O-]"
# Output: CC(=O)O

# Show step-by-step diff
smilesherlock standardize "[Na+].[OH-].CC(=O)[O-]" --show-diff

# Custom steps
smilesherlock standardize "O=C([O-])c1ccccc1" --steps neutralize,canonical

# Batch from CSV
smilesherlock standardize --file dirty.csv --output clean.csv
```

### Python API

```python
from smilesherlock import standardize_smiles

result = standardize_smiles("[Na+].[OH-].CC(=O)[O-]")
print(result.output_smiles)    # CC(=O)O
print(result.changed)          # True

# Inspect what changed per step
for s in result.step_results:
    if s.changed:
        print(f"{s.step}: {s.input_smiles} -> {s.output_smiles}")
```

---

## IUPAC Identifier Generation

Generate InChI, InChIKey, formula, MW offline. Fetch IUPAC systematic name via PubChem with local caching.

```bash
# Offline: InChI, InChIKey, formula, MW
smilesherlock iupacname "CC(=O)OC1=CC=CC=C1C(=O)O"

# With IUPAC name from PubChem (cached after first fetch)
smilesherlock iupacname "CCO" --online

# Batch
smilesherlock iupacname --file compounds.smi --online --output identifiers.csv
```

### Python API

```python
from smilesherlock import get_iupac_name

result = get_iupac_name("CCO", use_online=True)
print(result.inchi)              # InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3
print(result.inchikey)           # LFQSCWFLJHTTHZ-UHFFFAOYSA-N
print(result.molecular_formula)  # C2H6O
print(result.iupac_name)         # ethanol
print(result.iupac_name_source)  # pubchem (or 'cache' on repeat calls)
```

---
## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit changes (git commit -m 'Add amazing feature')
4. Push to branch (git push origin feature/amazing-feature)
5. Open a Pull Request

For more details, see the **[Contributing Guide](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/docs/contributing.md)**.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use SmileSherlock in your research, please cite:

```bibtex
@software{smilesherlock2026,
  author={Atharva Tilewale},
  doi={10.5281/zenodo.22065365},
  month={8},
  title={SmileSherlock: A High-Performance SMILES Validation and PubChem Lookup Tool},
  version={1.4.0},
  year={2026},
  url={https://github.com/AtharvaTilewale/SmileSherlock}
}
```

## Support

- **Documentation**: [https://smilesherlock.readthedocs.io](https://smilesherlock.readthedocs.io)
- **Issues**: [https://github.com/AtharvaTilewale/SmileSherlock/issues](https://github.com/AtharvaTilewale/SmileSherlock/issues)
- **Discussions**: [https://github.com/AtharvaTilewale/SmileSherlock/discussions](https://github.com/AtharvaTilewale/SmileSherlock/discussions)

## Changelog

See [CHANGELOG.md](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/CHANGELOG.md) for version history.

---

Made with ❤️ for the cheminformatics community
