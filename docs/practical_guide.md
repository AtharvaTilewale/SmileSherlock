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
- [6. Molecular Fingerprinting](#6-molecular-fingerprinting)
  - [CLI Examples](#cli-examples-2)
  - [Python API Examples](#python-api-examples-3)
- [7. Chemical Similarity Search](#7-chemical-similarity-search)
  - [CLI Examples](#cli-examples-3)
  - [Python API Examples](#python-api-examples-4)
- [8. Chemical Structure Filtering](#8-chemical-structure-filtering)
  - [CLI Examples](#cli-examples-4)
  - [Python API Examples](#python-api-examples-5)
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

```python
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

```bash
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

# 4. Chemical Structure Downloads & Generation

Download physical structure files from PubChem or generate 2D/3D conformations offline from SMILES using RDKit with built-in resume logic.

Supported Formats: `sdf`, `mol`, `pdb`, `png` (generation supports `sdf`, `mol`, `pdb`)

Supported Dimensions: `2d`, `3d`

Downloaded and generated files are skipped automatically unless `--force` is used.

```bash
# Download a single 3D SDF file by its PubChem CID
smilesherlock download 2244 --format sdf --3d

# Generate all 3D structures locally from SMILES using RDKit (--gen all)
smilesherlock download "CC(=O)OC1=CC=CC=C1C(=O)O" --gen all --3d --format sdf

# Generate 2D MOL structure locally from SMILES
smilesherlock download "c1ccccc1" --gen all --2d --format mol

# Batch download with fallback to local generation (--gen missing)
smilesherlock download -i my_compounds.csv --gen missing --format sdf --3d --output-dir ./structures/

# Batch generate all structures offline from file
smilesherlock download -i my_compounds.smi --gen all --format pdb --3d --output-dir ./3d_models/

# Force overwrite existing files (disables resume logic)
smilesherlock download -i my_compounds.csv --format sdf --force
```

## Python API Examples

```python
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

```python
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

---

# 6. Fingerprint Generation

Generate molecular fingerprints offline from SMILES strings. Useful for ML model preparation, similarity search, and database indexing.

## CLI

```bash
# Single compound - ECFP4 (default)
smilesherlock fingerprint "CC(=O)OC1=CC=CC=C1C(=O)O" --type ecfp4

# MACCS keys (167-bit)
smilesherlock fingerprint "CCO" --type maccs

# All fingerprint types at once
smilesherlock fingerprint "CC(=O)OC1=CC=CC=C1C(=O)O" --type all

# Batch file - save to CSV
smilesherlock fingerprint --file compounds.smi --type ecfp4 --bits 2048 --output fingerprints.csv

# Custom bit size
smilesherlock fingerprint "CC(=O)OC1=CC=CC=C1C(=O)O" --type rdkit --bits 1024
```

**Supported fingerprint types:**

| Type | Algorithm | Default Bits | Use Case |
|------|-----------|-------------|----------|
| `ecfp4` | Morgan (radius=2) | 2048 | General ML, virtual screening |
| `ecfp6` | Morgan (radius=3) | 2048 | More specific substructures |
| `fcfp4` | Feature Morgan (radius=2) | 2048 | Pharmacophore-based |
| `maccs` | MACCS Keys | 167 (fixed) | Structural keys, scaffold analysis |
| `rdkit` | Daylight-style RDKit | 2048 | General purpose |
| `atompair` | Atom Pair | 2048 | 3D-aware searches |
| `torsion` | Topological Torsion | 2048 | Conformer-sensitive searches |

## Python API

```python
from smilesherlock import compute_fingerprint

# Single fingerprint
fp = compute_fingerprint("CC(=O)OC1=CC=CC=C1C(=O)O", fp_type="ecfp4")
print(f"Type: {fp.fingerprint_type}, On bits: {fp.n_on_bits}, Density: {fp.density:.4f}")
print(f"Bit string: {fp.bit_string}")

# All fingerprint types
fps = compute_fingerprint("CCO", fp_type="all")
for fp in fps:
    print(f"{fp.fingerprint_type:12s}: {fp.n_on_bits} bits on / {fp.n_bits}")
```

---

# 7. Similarity Search

Search a compound library to find structurally similar compounds using Tanimoto similarity.

## CLI

```bash
# Search against a library file, default threshold 0.5, top 10
smilesherlock similar "CC(=O)OC1=CC=CC=C1C(=O)O" --file library.smi

# Custom threshold and top-N
smilesherlock similar "CC(=O)OC1=CC=CC=C1C(=O)O" --file library.csv --threshold 0.3 --top 20

# Use MACCS fingerprints instead of ECFP4
smilesherlock similar "CCO" --file compounds.smi --fp-type maccs --top 5

# Save results to CSV
smilesherlock similar "CC(=O)OC1=CC=CC=C1C(=O)O" --file library.smi --output hits.csv

# Higher bit resolution
smilesherlock similar "CCO" --file library.smi --fp-type ecfp6 --bits 4096 --top 10
```

## Python API

```python
from smilesherlock import compute_similarity

# Library as list of SMILES
library = ["CCO", "CCCO", "CC(=O)OC1=CC=CC=C1C(=O)O", "c1ccccc1", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"]

hits = compute_similarity(
    query_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
    library=library,
    fp_type="ecfp4",
    threshold=0.1,
    top_n=5,
)

for hit in hits:
    print(f"Rank {hit.rank}: {hit.hit} (Tanimoto={hit.similarity:.4f})")
```

---

# 8. Drug-Likeness Filtering (ADMET)

Evaluate compounds against standard drug-likeness rules and PAINS alerts.

## CLI

```bash
# Single compound - all rules (default)
smilesherlock filter "CC(=O)OC1=CC=CC=C1C(=O)O"

# Specific rules only
smilesherlock filter "CC(=O)OC1=CC=CC=C1C(=O)O" --rules lipinski,veber,pains

# Batch: keep only compounds that pass all rules
smilesherlock filter --file compounds.csv --rules lipinski --output drug_like.csv

# Batch: keep only PAINS-free compounds (--rules pains keeps clean ones)
smilesherlock filter --file compounds.csv --rules pains --output no_pains.csv

# Batch: keep only PAINS-flagged compounds for investigation (--fail inverts)
smilesherlock filter --file compounds.csv --rules pains --fail --output pains_hits.csv

# Add QED minimum threshold
smilesherlock filter --file compounds.csv --rules lipinski,veber --qed-min 0.5 --output output.csv
```

**Available filter rules:**

| Rule | Criteria | Use Case |
|------|----------|----------|
| `lipinski` | MW<=500, LogP<=5, HBD<=5, HBA<=10 | Oral drug candidates |
| `veber` | RotBonds<=10, TPSA<=140 A^2 | Oral bioavailability |
| `ghose` | MW 160-480, LogP -0.4 to 5.6, Atoms 20-70, MR 40-130 | Drug-like space |
| `egan` | TPSA<=131.6, LogP<=5.88 | Passive permeability |
| `ro3` | MW<=300, LogP<=3, HBD<=3, HBA<=3 | Lead-like fragments |
| `pains` | RDKit PAINS catalog | Frequent hitter detection |
| `qed` | 0-1 score (info only) | Overall drug-likeness score |

## Python API

```python
from smilesherlock import apply_filters

# All rules at once
result = apply_filters("CC(=O)OC1=CC=CC=C1C(=O)O")

print(f"MW:  {result.molecular_weight:.2f} g/mol")
print(f"LogP: {result.logp:.2f}")
print(f"QED:  {result.qed_score:.4f}")
print(f"Lipinski: {'PASS' if result.lipinski.passed else 'FAIL'} — {result.lipinski.details}")
print(f"PAINS:    {'PASS' if result.pains.passed else 'FAIL'} — {result.pains.details}")
print(f"Overall:  {'PASS' if result.passes_all else 'FAIL'}")

# Specific rules only
result = apply_filters("CC(=O)OC1=CC=CC=C1C(=O)O", rules=["lipinski", "pains"])

# Batch filtering
import csv

library = ["CC(=O)OC1=CC=CC=C1C(=O)O", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "c1ccccc1"]
passing = [smi for smi in library if apply_filters(smi, rules=["lipinski"]).passes_all]
print(f"Drug-like compounds: {len(passing)}/{len(library)}")
```
