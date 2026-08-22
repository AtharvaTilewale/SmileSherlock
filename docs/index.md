# SmileSherlock

<p align="center">
  <img src="https://raw.githubusercontent.com/AtharvaTilewale/SmileSherlock/main/docs/assets/smilesherlock-logo.png" alt="SmileSherlock logo" width="700" />
</p>

A high-performance, production-grade tool for SMILES validation, PubChem lookup, and chemical structure retrieval.

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
- **Offline Molecule Generation (--gen)** - Generate 2D and 3D conformations (SDF, MOL, PDB) offline
- **Molecular Fingerprints** *(v1.3.0)* - ECFP4, ECFP6, FCFP4, MACCS, RDKit, AtomPair, Torsion offline (`fingerprint` command)
- **Similarity Search** *(v1.3.0)* - Tanimoto-based library search with threshold and top-N (`similar` command)
- **Drug-Likeness Filtering** *(v1.3.0)* - Lipinski, Veber, Ghose, Egan, Ro3, PAINS, QED (`filter` command) from SMILES via RDKit with forcefield optimization
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

### Python API

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

For more detailed API documentation, see the **[API Reference](api_reference.md)** page.

## Documentation

For complete tutorials and advanced usage examples, see the **[Practical Guide](practical_guide.md)**

## Requirements

- Python 3.10+
- RDKit (cheminformatics library)
- pandas (data handling)
- requests/aiohttp (HTTP)
- typer (CLI framework)
- rich/tqdm (UI/progress)

## Configuration

For configuration and architecture details, see the **[Configuration & Architecture](configuration.md)** page.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit changes (git commit -m 'Add amazing feature')
4. Push to branch (git push origin feature/amazing-feature)
5. Open a Pull Request

For more details, see the **[Contributing Guide](contributing.md)**.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use SmileSherlock in your research, please cite:

```bibtex
@software{smilesherlock2026,
  author={Atharva Tilewale},
  title={SmileSherlock: High-performance SMILES validation and PubChem lookup},
  version={1.2.0},
  year={2026},
  url={https://github.com/AtharvaTilewale/SmileSherlock}
}
``` 

## Support

- **Documentation**: [https://smilesherlock.readthedocs.io](https://smilesherlock.readthedocs.io)
- **Issues**: [https://github.com/AtharvaTilewale/SmileSherlock/issues](https://github.com/AtharvaTilewale/SmileSherlock/issues)
- **Discussions**: [https://github.com/AtharvaTilewale/SmileSherlock/discussions](https://github.com/AtharvaTilewale/SmileSherlock/discussions)

## Changelog

See [CHANGELOG.md](changelog.md) for version history.

---

Made with ❤️ for the cheminformatics community
