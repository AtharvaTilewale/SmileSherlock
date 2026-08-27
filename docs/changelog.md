# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-08-27

### Added
- **`rgroup` command**: Perform R-Group Decomposition against a common core SMARTS.
- **`augment` command**: Generate uncanonical/randomized SMILES strings for ML data augmentation.
- **`atommap` command**: Assign unique atom mapping numbers to all atoms in a molecule.
- Exported new core API modules: `rgroup.py`, `augment.py`, and `atommap.py`.

### Tests
- Added `tests/test_rgroup.py` with 11 tests for R-Group decomposition.
- Added `tests/test_augment.py` with 10 tests for SMILES augmentation.
- Added `tests/test_atommap.py` with 10 tests for atom mapping.

## [1.6.0] - 2026-08-24

### Added
- **`reaction` command**: Validate and analyze Reaction SMILES (SMIRKS) strings.
- **`conformers` command**: Generate multiple 3D conformers using RDKit's ETKDG algorithm and MMFF optimization, exported as multi-model `.sdf`.
- **`scaffold` command**: Extract the Murcko Scaffold framework from a SMILES string (supports batch processing).
- **`stereo` command**: Analyze a SMILES string for assigned and unassigned stereocenters, with optional `--chiral-flag` enforcement.
- Exported new modules: `reaction.py`, `conformers.py`, `scaffold.py`, and `stereo.py` to the core API.

### Tests
- Added `tests/test_reaction.py` with 10 tests for reaction validation.
- Added `tests/test_conformers.py` with 14 tests for conformer generation.
- Added `tests/test_scaffold.py` with 9 tests for scaffold extraction.
- Added `tests/test_stereo.py` with 10 tests for stereocenter analysis.
- Total: 151 offline tests passing (+ 10 integration tests).

## [1.5.0] - 2026-08-24

### Added
- **`tautomers` command**: Enumerate all plausible tautomers for a given SMILES string.
  - Critical for protein-ligand docking preparation.
  - Exposes RDKit's `MolStandardize.TautomerEnumerator`.
  - Batch processing support with `--file` and `--output` (exports one row per tautomer, exploding the dataset).
  - New Python API `enumerate_tautomers()` returning `TautomerResult`.

- **`substructure` command**: Search a library for compounds containing a specific molecular fragment or functional group.
  - Uses RDKit's `HasSubstructMatch` algorithm.
  - Supports both SMARTS (default) and strict SMILES queries (`--smiles-query`).
  - Batch processing support with `--file` and `--output` to save matching compounds.
  - New Python API `substructure_search()` returning `SubstructureHit`.

## [1.4.0] - 2026-08-23

### Added
- **`standardize` command** - Full offline SMILES standardization pipeline using RDKit `MolStandardize`:
  - **Salt stripping** (`fragment` step): Keeps the largest organic fragment, removes counterions/salts.
  - **Neutralization** (`neutralize` step): Neutralizes charged atoms (e.g., carboxylates -> carboxylic acids).
  - **Tautomer canonicalization** (`tautomer` step): Normalizes tautomers to a single canonical form.
  - **Canonical SMILES** (`canonical` step): Outputs canonical RDKit SMILES.
  - `--steps`: Choose individual steps (e.g., `--steps fragment,neutralize`) or `all` (default).
  - `--show-diff`: Step-by-step breakdown showing exactly what changed at each stage.
  - `--file` / `--output`: Batch CSV/SMI processing with CSV output.
- **`iupacname` command** - Systematic IUPAC identifier generation from SMILES:
  - **Fully offline**: InChI, InChIKey, Molecular Formula, Exact MW — always computed locally via RDKit.
  - **PubChem IUPAC name** (`--online`): Fetches the preferred IUPAC name from PubChem REST API.
  - **Local SQLite caching**: After a first `--online` lookup, subsequent calls return the cached name offline.
  - `--file` / `--output`: Batch CSV/SMI processing with CSV output.
- New public API exports: `standardize_smiles`, `StandardizeResult`, `StepResult`, `STANDARDIZE_STEPS`,
  `get_iupac_name`, `IUPACResult`

### Tests
- Added `tests/test_standardize_iupac.py` with 33 tests (31 offline, 2 integration).
- Total: 107 offline tests passing (+ 10 integration tests).

## [1.3.0] - 2026-08-23

### Added
- **`fingerprint` command** — Generate ECFP4, ECFP6, FCFP4, MACCS, RDKit, AtomPair, and Topological Torsion fingerprints from SMILES (offline, RDKit-based). Supports single compounds and batch file processing with CSV export.
- **`similar` command** — Tanimoto-based similarity search: compare a query SMILES against a compound library file. Supports all fingerprint types, configurable threshold, and top-N ranking with optional CSV output.
- **`filter` command** — Drug-likeness and ADMET evaluation with six rules: Lipinski Ro5, Veber oral bioavailability, Ghose filter, Egan passive permeability, Rule of Three (lead-like), PAINS alert detection. Also computes QED score. Supports `--fail` flag to invert selection and `--qed-min` threshold for batch filtering.
- **New core module** `smilesherlock/core/cheminfo.py` with three public functions:
  - `compute_fingerprint(smiles, fp_type, n_bits)` — returns `FingerprintResult` or `List[FingerprintResult]`
  - `apply_filters(smiles, rules)` — returns `FilterResult` with per-rule `RuleResult` objects
  - `compute_similarity(query_smiles, library, fp_type, n_bits, threshold, top_n)` — returns `List[SimilarityResult]`
- **New Pydantic models**: `FingerprintResult`, `FilterResult`, `RuleResult`, `SimilarityResult` — all exported from the top-level package
- 49 new unit tests in `tests/test_cheminfo.py` (77 total across the test suite, all passing)
- Updated `docs/api_reference.md`, `docs/practical_guide.md` (Sections 6–8), `README.md`, and `docs/index.md`

### Changed
- Version bumped to `1.3.0`

## [1.2.0] - 2026-08-23

### Added
- **Offline Molecular Structure Generation (--gen)**: Generate 2D and 3D conformations directly from SMILES using RDKit with forcefield energy minimization (MMFF94 / UFF).
  - --gen all: Generate 2D/3D structures locally for all input compounds.
  - --gen missing: Seamlessly download from PubChem when available, automatically generating structures locally when missing or not in database.
- **Multi-Format Conformations**: Support for .sdf, .mol, and .pdb output formats with --3d and --2d coordinate options.
- **Python API**: Exported generate_structure() at the package root for programmatic offline conformation generation.

### Fixed
- Fixed PubChem compound SQLite caching attribute resolution for isomeric_smiles.
- Improved CLI table formatting and command registration.

## [1.1.0] - 2026-08-02

### Added
- **Lookup by Name:** Added explicit PubChem querying by chemical name.
- **Smart Auto-Routing:** The CLI `auto` mode now seamlessly falls back to name-based lookup if an invalid SMILES string is provided.
- **Python API:** Exposed `lookup_by_name()` directly at the package root.

### Fixed
- Silenced aggressive C++ terminal warnings from RDKit when auto-parsing non-SMILES inputs.
- Fixed a SQLite caching bug where `canonical_smiles` was being referenced using an outdated attribute name.
- Cleaned up redundant CLI warnings for a smoother user experience.
- Fixed a bug where the `--3d` and `--2d` flags in the `download` command incorrectly required additional string arguments. 


## [1.0.0] - 2026-08-02

### Added
- **Initial Release of SmileSherlock!**
- **Core Engine:** RDKit-powered SMILES validation and canonicalization.
- **PubChem Integration:** Single and batch lookups via the PubChem PUG REST API.
- **Multi-format Support:** Auto-parsing for `.csv`, `.tsv`, `.xlsx`, `.smi`, and `.sdf` files with smart column detection.
- **Structure Downloads:** Automated downloading of 2D/3D structures in `sdf`, `mol`, `pdb`, and `png` formats with built-in resume logic.
- **High Performance:** Multithreading architecture using `concurrent.futures` for lightning-fast batch processing.
- **Smart Rate Limiting:** Thread-safe API limiter to respect PubChem server limits.
- **Caching:** Local SQLite database to permanently store results and eliminate redundant API calls.
- **Reporting:** Rich progress bars and auto-generated `.log` files detailing the success or failure of batch queries.
- **CLI Commands:** `init`, `status`, `lookup`, `batch`, `download`, `update`, and `reinstall`.
- **Smart Updater:** Seamlessly fetch and apply code updates directly from GitHub or PyPI via `smilesherlock update`.