"""Tests for SMILES validation and RDKit descriptors."""

from smilesherlock.core.smiles import validate_smiles


def test_valid_smiles() -> None:
    """Test validation of valid SMILES."""
    result = validate_smiles("c1ccccc1")
    assert result.is_valid is True
    assert result.canonical_smiles == "c1ccccc1"
    assert result.molecular_formula == "C6H6"
    assert result.molecular_weight is not None
    assert result.molecular_weight > 78.0


def test_invalid_smiles() -> None:
    """Test validation of invalid SMILES."""
    result = validate_smiles("invalid_smiles_string_123")
    assert result.is_valid is False
    assert result.error_message is not None