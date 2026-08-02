# SmileSherlock

<p align="center">
  <img src="./docs/assets/smilesherlock-logo.png" alt="SmileSherlock Logo" width="800" />
</p>

<p align="center">
  <b>A high-performance, production-grade toolkit for SMILES validation, PubChem lookup, and chemical structure retrieval.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/smilesherlock/"><img src="https://img.shields.io/pypi/v/smilesherlock.svg" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License"></a>
</p>

---

## Features

- ✅ **SMILES Validation & Canonicalization** using RDKit
- ✅ **Multi-format Input** (CSV, TSV, TXT, XLSX, SMI, SDF)
- ✅ **Automatic SMILES Column Detection**
- ✅ **PubChem Lookup** by SMILES, CID, Name, InChI, and InChIKey
- ✅ **Rich Metadata Retrieval**
  - CID
  - IUPAC Name
  - Molecular Formula
  - Molecular Weight
  - Exact Mass
  - InChI
  - InChIKey
  - Canonical & Isomeric SMILES
  - Molecular Descriptors
- ✅ **Structure Downloads**
  - 2D / 3D SDF
  - MOL
  - PDB
  - PNG
- ✅ **Batch Processing**
- ✅ **Multithreaded Downloads & Lookups**
- ✅ **SQLite Caching**
- ✅ **Detailed Log Files**
- ✅ **CSV / Excel / JSON Export**
- ✅ **Python API**
- ✅ **Command Line Interface**
- ✅ **Smart Updater & Reinstaller**

---

# Installation

## Install from PyPI

```bash
pip install smilesherlock
```

---

## Development Installation

```bash
git clone https://github.com/AtharvaTilewale/SmileSherlock.git

cd SmileSherlock

pip install -e ".[dev]"
```

---

# Quick Start

## Show Status

```bash
smilesherlock status
```

## Initialize Database & Directories

```bash
smilesherlock init
```

## Update

```bash
smilesherlock update
```

## Reinstall

```bash
smilesherlock reinstall
```

---

## Lookup Single Compound

Using SMILES

```bash
smilesherlock lookup "c1ccccc1"
```

Using CID

```bash
smilesherlock lookup 241 --cid
```

---

## Batch Lookup

```bash
smilesherlock batch compounds.csv \
    --output results.xlsx \
    --format xlsx
```

---

## Download Structures

Single Compound

```bash
smilesherlock download 241 \
    --format sdf \
    --3d
```

Batch Download

```bash
smilesherlock download \
    -i compounds.csv \
    --format pdb \
    --2d
```

---

# Python API

```python
from smilesherlock import (
    lookup,
    lookup_file,
    download_structure,
)

result = lookup("c1ccccc1")

print(result.cid)
print(result.iupac_name)

lookup_file(
    "compounds.csv",
    output_format="xlsx",
)

download_structure(
    cid=241,
    format="sdf",
    dimension="3d",
)
```

---

# Requirements

- Python ≥ 3.10
- RDKit
- pandas
- requests
- typer
- rich
- openpyxl

---

# Configuration

Environment variables are supported.

```bash
export SMILESHERLOCK_CACHE_DIR=/custom/cache

export SMILESHERLOCK_LOG_LEVEL=DEBUG

export SMILESHERLOCK_MAX_WORKERS=8
```

Configuration priority:

1. Environment variables
2. `.env`
3. Built-in defaults

---

# Project Structure

```text
SmileSherlock/
│
├── smilesherlock/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── logging_config.py
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── core/
│   │   ├── smiles.py
│   │   ├── pubchem.py
│   │   └── database.py
│   │
│   └── utils/
│       ├── file_io.py
│       ├── export.py
│       └── parsers.py
│
├── docs/
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

---

# Roadmap

## Phase 1 — Foundation

- [x] Project structure
- [x] CLI
- [x] Configuration
- [x] Logging
- [x] Installable package

---

## Phase 2 — Core Lookup

- [x] RDKit validation
- [x] PubChem API
- [x] SQLite cache
- [x] Metadata retrieval
- [x] Unit tests

---

## Phase 3 — Batch Processing

- [x] CSV / TSV / XLSX / SDF parsing
- [x] Automatic SMILES detection
- [x] Batch lookup
- [x] Export formats

---

## Phase 4 — Structure Downloads

- [x] 2D & 3D structures
- [x] SDF
- [x] MOL
- [x] PDB
- [x] PNG
- [x] Resume downloads

---

## Phase 5 — Advanced Features

- [x] Multithreading
- [x] Retry logic
- [x] Python API
- [x] Advanced caching
- [x] Auto updater
- [x] Reinstaller

---

## Phase 6 — Release

- [ ] Full test coverage
- [ ] Integration tests
- [ ] GitHub Actions
- [ ] Code coverage
- [ ] PyPI release
- [ ] Documentation

---

# Contributing

Contributions are welcome.

```bash
git checkout -b feature/my-feature

git commit -m "Add new feature"

git push origin feature/my-feature
```

Then open a Pull Request.

---

# Citation

If you use **SmileSherlock** in your research, please cite:

```bibtex
@software{smilesherlock2026,
  author  = {Atharva Tilewale},
  title   = {SmileSherlock: High-Performance SMILES Validation and PubChem Lookup},
  version = {1.0.0},
  year    = {2026},
  url     = {https://github.com/AtharvaTilewale/SmileSherlock}
}
```

---

# License

Released under the MIT License.

See the **LICENSE** file.

---

# Support

- 📖 Documentation *(Coming Soon)*
- 🐛 Issues: https://github.com/AtharvaTilewale/SmileSherlock/issues
- 💬 Discussions: https://github.com/AtharvaTilewale/SmileSherlock/discussions

---

# Changelog

See **CHANGELOG.md**.

---

<p align="center">
Made with ❤️ for the cheminformatics community.
</p>