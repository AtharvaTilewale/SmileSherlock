# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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