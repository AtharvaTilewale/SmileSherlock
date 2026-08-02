# SmileSherlock Practical Guide (v1.1.0)

Welcome to the comprehensive tutorial for **SmileSherlock**. This guide is designed to take you from basic lookups to advanced, multithreaded batch processing using both the Command Line Interface (CLI) and the Python API.

---

# Table of Contents

- [SmileSherlock Practical Guide (v1.1.0)](#smilesherlock-practical-guide-v110)
- [Table of Contents](#table-of-contents)
- [1. System Management](#1-system-management)
    - [CLI Commands](#cli-commands)
- [2. Single Compound Lookups](#2-single-compound-lookups)
  - [CLI Examples](#cli-examples)
    - [Basic Lookups:](#basic-lookups)
    - [Advanced CLI Flags:](#advanced-cli-flags)
    - [Python API Examples](#python-api-examples)
- [3. Batch Processing \& File I/O](#3-batch-processing--file-io)
  - [CLI Examples](#cli-examples-1)
  - [Python API Examples](#python-api-examples-1)
- [4. Chemical Structure Downloads](#4-chemical-structure-downloads)
  - [Python API Examples](#python-api-examples-2)
- [5. Advanced SMILES Validation (Python API)](#5-advanced-smiles-validation-python-api)
- [Learn More](#learn-more)

---

# 1. System Management

SmileSherlock manages local SQLite caches and logs to ensure high performance and respect for PubChem's rate limits.

### CLI Commands

Check your environment paths, active threads, and database size:

```bash
smilesherlock status
```

Initialize the database schema and storage directories (Run this once after installation):

```bash
smilesherlock init
```

Keep your tool up-to-date. This smart command automatically checks PyPI (or GitHub if you cloned the source) and safely applies updates:

```bash
smilesherlock update
```

If your local database gets corrupted or you want to clear your cache completely, perform a factory reset:

```bash
smilesherlock reinstall -y
```

---

# 2. Single Compound Lookups

SmileSherlock's "Smart Auto-Routing" automatically detects if your input is a SMILES string, an InChIKey, a PubChem CID, or a Chemical Name.

## CLI Examples

### Basic Lookups:

```bash
# Lookup by SMILES
smilesherlock lookup "CC(=O)OC1=CC=CC=C1C(=O)O"

# Lookup by Common/IUPAC Name
smilesherlock lookup "Aspirin"
smilesherlock lookup "benzene"
```

### Advanced CLI Flags:

```bash
# Bypass the local SQLite cache to force a fresh network request
smilesherlock lookup "Caffeine" --no-cache

# Force the engine to treat the input specifically as a CID
smilesherlock lookup 2244 --cid

# Output raw JSON instead of a rich table (ideal for piping into `jq` or other scripts)
smilesherlock lookup "Ibuprofen" --json
```

### Python API Examples

```
from smilesherlock import lookup, lookup_by_name

# 1. Smart Auto-Detect Lookup
compound = lookup("c1ccccc1")
print(f"Name: {compound.iupac_name}, MW: {compound.molecular_weight}")

# 2. Explicit Lookup by Name (Bypasses SMILES validation checks)
drug = lookup_by_name("Amoxicillin")
print(f"CID: {drug.cid}, Formula: {drug.molecular_formula}")

# 3. Accessing detailed properties (PubChemCompound model)
if drug:
    print(f"H-Bond Donors: {drug.hbond_donor_count}")
    print(f"XLogP: {drug.xlogp}")
    print(f"InChIKey: {drug.inchikey}")
```

---

# 3. Batch Processing & File I/O

Process hundreds of compounds in seconds. SmileSherlock uses multithreading (`concurrent.futures`) combined with a strict rate limiter to fetch data as fast as possible without getting banned by PubChem.

Supported Input Formats: `.csv`, `.tsv`, `.xlsx`, `.smi`, `.sdf`, `.txt`

(SmileSherlock automatically detects the column containing SMILES/Names!)

## CLI Examples

```
# Basic batch processing (auto-generates a CSV output and a .log report)
smilesherlock batch input_data.csv

# Output to an Excel file and keep duplicate entries (duplicates are removed by default)
smilesherlock batch raw_smiles.txt --format xlsx --keep-duplicates

# Specify a custom output path and export as JSON
smilesherlock batch data.sdf --output /my_project/clean_data.json --format json
```

## Python API Examples

```python
from smilesherlock import lookup_file, lookup

# 1. Process a file directly in your script
results = lookup_file(
    input_file="messy_data.csv",
    output_file="clean_results.xlsx",
    output_format="xlsx",
    remove_duplicates=True
)

print(f"Successfully processed {len(results)} unique compounds.")

# 2. Custom loop for lists (No file needed)
my_chemicals = ["Aspirin", "c1ccccc1", "Invalid_Chemical_Name"]
valid_compounds = []

for chem in my_chemicals:
    data = lookup(chem, use_cache=True)
    if data and data.cid:
        valid_compounds.append(data)
```

---

# 4. Chemical Structure Downloads

Download physical structure files with built-in resume logic (it skips files you've already downloaded).

Supported Formats: `sdf`, `mol`, `pdb`, `png`

Supported Dimensions: `2d`, `3d`

Downloaded files are skipped automatically unless `--force` is used.

```
# Download a single 3D SDF file by its PubChem CID
smilesherlock download 2244 --format sdf --3d

# Save a 2D PNG image to a specific folder
smilesherlock download 2244 --format png --2d --output-dir ./images/

# Batch download 3D PDB files from a list of names/SMILES in a CSV
smilesherlock download -i my_compounds.csv --format pdb --3d --output-dir ./3d_models/

# Force overwrite existing files (disables resume logic)
smilesherlock download -i my_compounds.csv --format sdf --force
```

## Python API Examples

```
from smilesherlock import download_structure

# Download a single structure programmatically
status = download_structure(
    cid=2244, 
    format="sdf", 
    dimension="3d", 
    output_dir="my_structures",
    force=False
)

print(f"Download status: {status}")
```

# 5. Advanced SMILES Validation (Python API)

If you only need to validate SMILES strings and calculate RDKit descriptors locally without querying the PubChem internet database, you can use the core SMILES engine directly.

```
from smilesherlock import validate_smiles

# Validate a complex SMILES string
result = validate_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")

if result.is_valid:
    print(f"Standardized SMILES: {result.canonical_smiles}")
    print(f"Exact Mass: {result.molecular_weight}")
    print(f"Heavy Atoms: {result.heavy_atom_count}")
    print(f"TPSA: {result.tpsa}")
    print(f"Calculated LogP: {result.logp}")
else:
    print(f"Invalid SMILES! Error: {result.error_message}")
```

---

# Learn More

- **[README.md](https://github.com/AtharvaTilewale/SmileSherlock/blob/main/README.md)** — Installation and Quick Start
- **[API Documentation](https://smilesherlock.readthedocs.io/en/latest/)** — Python API reference
- **[GitHub Issues](https://github.com/AtharvaTilewale/SmileSherlock/issues)** — Bug reports and feature requests
- **[Discussions](https://github.com/AtharvaTilewale/SmileSherlock/discussions)** — Community support