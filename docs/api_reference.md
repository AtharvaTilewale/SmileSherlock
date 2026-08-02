# API Reference

This page details the core public functions and data models exposed by the `smilesherlock` package. All core functions can be imported directly from the top-level package.

```python
from smilesherlock import lookup, lookup_by_name, lookup_file, validate_smiles
```

The primary router for fetching chemical data. It auto-detects the format of the query and routes it to the appropriate PubChem endpoint.

- ### Parameters:
    - `query` (str | int): The identifier to search for (SMILES, CID, InChIKey, or Name).
    - `search_type` (str, optional): Override auto-detection. Valid options are "`auto`", "`cid`", "`smiles`", "`name`", or "`inchikey`". Defaults to "`auto`".
    - `use_cache` (bool, optional): Whether to check the local SQLite database before making a network request. Defaults to `True`.

- ### Returns:
    - `PubChemCompound` if found, otherwise `None`.

`lookup_by_name()`

```python
def lookup_by_name(name: str, use_cache: bool = True) -> Optional[PubChemCompound]
```

Explicitly queries PubChem by a common or IUPAC chemical name. This bypasses all SMILES validation checks.

- ### Parameters:

    - `name` (str): The chemical name (e.g., "`Aspirin`", "`Benzene`").

    - `use_cache` (bool, optional): Defaults to `True`.

- ### Returns:

    - `PubChemCompound` if found, otherwise `None`.

`lookup_file()`

```python
def lookup_file(input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None, output_format: str = "csv", remove_duplicates: bool = True) -> List[PubChemCompound]
```

Processes a batch file of compounds using multithreading.

- ### Parameters:

    - `input_file` (str | Path): Path to the input file (`.csv`, `.tsv`, `.xlsx`, `.smi`, `.sdf`).

    - `output_file` (str | Path, optional): Path to save the results. If `None`, results are kept in memory.

    - `output_format` (str, optional): Format to export ("`csv`", "`xlsx`", "`json`").

    - `remove_duplicates` (bool, optional): Automatically dedupes the input list to save API calls. Defaults to `True`.

- ### Returns:

    - A list of `PubChemCompound` objects.
  
`download_structure()`

```python
def download_structure(cid: int, format: str = "sdf", dimension: str = "3d", output_dir: str = "structures", force: bool = False) -> str
```

Downloads physical structure files directly from PubChem. Features smart-resume to skip existing files.

- ### Parameters:

    - `cid` (int): The PubChem CID.

    - `format` (str, optional): "`sdf`", "`mol`", "`pdb`", or "`png`". Defaults to "`sdf`".

    - `dimension` (str, optional): "`2d`" or "`3d`". Defaults to "`3d`".

    - `output_dir` (str, optional): The folder to save structures in. Defaults to "`structures`".

    - `force` (bool, optional): Overwrite existing files. Defaults to `False`.

- ### Returns:

A status string ("`Downloaded`", "`Skipped`", or error message).

`validate_smiles()`

```python
def validate_smiles(smiles_str: str) -> SMILESValidationResult
```

Performs high-speed, offline SMILES validation and physicochemical descriptor calculation using the local RDKit engine. Does not connect to the internet.

- ### Parameters:

    - `smiles_str` (str): The SMILES string to validate.

- ### Returns:

    - A `SMILESValidationResult` object.

## Data Models

SmileSherlock uses [Pydantic](https://pydantic-docs.helpmanual.io/) models to strictly type and validate returned data.


`PubChemCompound`

The core object returned by all `lookup` methods.

| Attribute | Type | Description |
|-----------|------|-------------|
| `input_query` | `str` | The original string used to search for this compound. |
| `cid` | `int` | The official PubChem Compound ID. |
| `title` | `str` | The common title of the compound. |
| `iupac_name` | `str` | The IUPAC standardized name. |
| `molecular_formula` | `str` | The chemical formula (e.g., `C6H6`). |
| `molecular_weight` | `float` | Exact molecular weight in g/mol. |
| `canonical_smiles` | `str` | PubChem's standardized canonical SMILES. |
| `isomeric_smiles` | `str` | PubChem's standardized isomeric SMILES. |
| `inchikey` | `str` | The 27-character InChIKey. |
| `inchi` | `str` | The full InChI string. |
| `xlogp` | `float` | Calculated lipophilicity (XLogP3). |
| `hbond_donor_count` | `int` | Number of hydrogen bond donors. |
| `hbond_acceptor_count` | `int` | Number of hydrogen bond acceptors. |

`SMILESValidationResult`

The object returned by the offline `validate_smiles()` function.

| Attribute | Type | Description |
|-----------|------|-------------|
| `is_valid` | `bool` | `True` if RDKit successfully parsed the SMILES string. |
| `canonical_smiles` | `str` | RDKit-standardized canonical SMILES. |
| `logp` | `float` | RDKit-calculated MolLogP value. |
| `tpsa` | `float` | Topological Polar Surface Area (TPSA). |
| `heavy_atom_count` | `int` | Total number of heavy (non-hydrogen) atoms. |
| `error_message` | `str` | Error message returned if `is_valid` is `False`. |