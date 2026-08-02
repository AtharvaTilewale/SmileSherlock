# SmileSherlock Practical Guide (v1.1.0)

Welcome to the comprehensive tutorial for **SmileSherlock**. This guide will take you from basic compound lookups to advanced multithreaded batch processing using both the **Command Line Interface (CLI)** and the **Python API**.

---

# Table of Contents

1. [System Management](#1-system-management)
2. [Single Compound Lookups](#2-single-compound-lookups)
3. [Batch Processing & File I/O](#3-batch-processing--file-io)
4. [Chemical Structure Downloads](#4-chemical-structure-downloads)
5. [Advanced SMILES Validation (Python API)](#5-advanced-smiles-validation-python-api)

---

# 1. System Management

SmileSherlock maintains a local SQLite cache and log files to improve performance while respecting PubChem rate limits.

## Check Status

```bash
smilesherlock status
```

Displays:

- Configuration
- Cache directory
- Database location
- Active thread count
- Version information

---

## Initialize

Run once after installation.

```bash
smilesherlock init
```

This creates:

- SQLite database
- Cache directory
- Log directory

---

## Update

Automatically checks for updates on PyPI (or GitHub if installed from source).

```bash
smilesherlock update
```

---

## Factory Reset

Clear cache and recreate the local environment.

```bash
smilesherlock reinstall --yes
```

---

# 2. Single Compound Lookups

SmileSherlock automatically detects whether the input is:

- SMILES
- Compound Name
- PubChem CID
- InChI
- InChIKey

---

## CLI Examples

### Lookup by SMILES

```bash
smilesherlock lookup "CC(=O)OC1=CC=CC=C1C(=O)O"
```

### Lookup by Name

```bash
smilesherlock lookup "Aspirin"

smilesherlock lookup "Benzene"
```

### Ignore Local Cache

```bash
smilesherlock lookup "Caffeine" --no-cache
```

### Force CID Lookup

```bash
smilesherlock lookup 2244 --cid
```

### JSON Output

```bash
smilesherlock lookup "Ibuprofen" --json
```

---

## Python API

```python
from smilesherlock import lookup, lookup_by_name

# Smart auto-detect
compound = lookup("c1ccccc1")

print(compound.iupac_name)
print(compound.molecular_weight)

# Explicit lookup by compound name
drug = lookup_by_name("Amoxicillin")

print(drug.cid)
print(drug.molecular_formula)

# Access additional properties
print(drug.hbond_donor_count)
print(drug.xlogp)
print(drug.inchikey)
```

---

# 3. Batch Processing & File I/O

SmileSherlock processes hundreds of compounds using multithreading together with built-in rate limiting.

## Supported Input Formats

- CSV
- TSV
- XLSX
- TXT
- SMI
- SDF

SMILES and compound name columns are detected automatically.

---

## CLI Examples

### Basic Batch Processing

```bash
smilesherlock batch input_data.csv
```

### Export to Excel

```bash
smilesherlock batch raw_smiles.txt \
    --format xlsx \
    --keep-duplicates
```

### Export JSON

```bash
smilesherlock batch data.sdf \
    --output /my_project/clean_data.json \
    --format json
```

---

## Python API

```python
from smilesherlock import lookup_file, lookup

results = lookup_file(
    input_file="messy_data.csv",
    output_file="clean_results.xlsx",
    output_format="xlsx",
    remove_duplicates=True,
)

print(f"Processed {len(results)} compounds.")
```

### Custom Processing

```python
from smilesherlock import lookup

chemicals = [
    "Aspirin",
    "c1ccccc1",
    "Invalid_Chemical_Name",
]

valid = []

for compound in chemicals:
    result = lookup(compound)

    if result and result.cid:
        valid.append(result)

print(len(valid))
```

---

# 4. Chemical Structure Downloads

Supported formats

- SDF
- MOL
- PDB
- PNG

Supported dimensions

- 2D
- 3D

Downloaded files are skipped automatically unless `--force` is used.

---

## CLI Examples

### Download Single Structure

```bash
smilesherlock download 2244 \
    --format sdf \
    --3d
```

### Download PNG

```bash
smilesherlock download 2244 \
    --format png \
    --2d \
    --output-dir ./images
```

### Batch Download

```bash
smilesherlock download \
    -i my_compounds.csv \
    --format pdb \
    --3d \
    --output-dir ./3d_models
```

### Overwrite Existing Files

```bash
smilesherlock download \
    -i my_compounds.csv \
    --format sdf \
    --force
```

---

## Python API

```python
from smilesherlock import download_structure

status = download_structure(
    cid=2244,
    format="sdf",
    dimension="3d",
    output_dir="my_structures",
    force=False,
)

print(status)
```

---

# 5. Advanced SMILES Validation (Python API)

Use SmileSherlock as a lightweight RDKit validation engine without querying PubChem.

```python
from smilesherlock import validate_smiles

result = validate_smiles(
    "CC(=O)OC1=CC=CC=C1C(=O)O"
)

if result.is_valid:
    print(result.canonical_smiles)
    print(result.molecular_weight)
    print(result.heavy_atom_count)
    print(result.tpsa)
    print(result.logp)
else:
    print(result.error_message)
```

---

# Learn More

- **[README.md](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/README.md)** — Installation and Quick Start
- **[API Documentation](https://smilesherlock.readthedocs.io/en/latest/)** — Python API reference
- **[GitHub Issues](https://github.com/AtharvaTilewale/SmileSherlock/issues)** — Bug reports and feature requests
- **[Discussions](https://github.com/AtharvaTilewale/SmileSherlock/discussions)** — Community support