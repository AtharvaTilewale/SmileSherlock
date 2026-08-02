# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-02

### Added
- **Lookup by Name:** Added explicit PubChem querying by chemical name.
- **Smart Auto-Routing:** The CLI `auto` mode now seamlessly falls back to name-based lookup if an invalid SMILES string is provided.
- **Python API:** Exposed `lookup_by_name()` directly at the package root.

### Fixed
- Silenced aggressive C++ terminal warnings from RDKit when auto-parsing non-SMILES inputs.
- Fixed a SQLite caching bug where `canonical_smiles` was being referenced using an outdated attribute name.
- Cleaned up redundant CLI warnings for a smoother user experience.


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