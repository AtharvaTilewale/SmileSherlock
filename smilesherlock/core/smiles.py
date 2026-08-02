"""SMILES validation and chemical property calculation utilities using RDKit."""

from typing import Optional
from pydantic import BaseModel, Field

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit import RDLogger
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

RDLogger.DisableLog('rdApp.*') 

class SMILESValidationResult(BaseModel):
    """Result model for SMILES validation and property extraction."""

    input_smiles: str
    is_valid: bool
    canonical_smiles: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = Field(None, description="H-Bond Donors")
    hba: Optional[int] = Field(None, description="H-Bond Acceptors")
    tpsa: Optional[float] = Field(None, description="Topological Polar Surface Area")
    heavy_atom_count: Optional[int] = None
    error_message: Optional[str] = None


def validate_smiles(smiles_str: str) -> SMILESValidationResult:
    """
    Validate and canonicalize a SMILES string, returning chemical descriptors.

    Args:
        smiles_str: Input SMILES string to validate.

    Returns:
        SMILESValidationResult object.
    """
    if not smiles_str or not isinstance(smiles_str, str):
        return SMILESValidationResult(
            input_smiles=str(smiles_str),
            is_valid=False,
            error_message="Empty or invalid input type",
        )

    smiles_clean = smiles_str.strip()

    if not RDKIT_AVAILABLE:
        return SMILESValidationResult(
            input_smiles=smiles_clean,
            is_valid=True,
            canonical_smiles=smiles_clean,
            error_message="RDKit is not installed; skipping detailed validation",
        )

    mol = Chem.MolFromSmiles(smiles_clean)
    if mol is None:
        return SMILESValidationResult(
            input_smiles=smiles_clean,
            is_valid=False,
            error_message="RDKit failed to parse SMILES string",
        )

    try:
        canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
        mw = float(Descriptors.ExactMolWt(mol))
        formula = rdMolDescriptors.CalcMolFormula(mol)
        logp = float(Descriptors.MolLogP(mol))
        hbd = int(rdMolDescriptors.CalcNumHBD(mol))
        hba = int(rdMolDescriptors.CalcNumHBA(mol))
        tpsa = float(Descriptors.TPSA(mol))
        heavy_atoms = int(mol.GetNumHeavyAtoms())

        return SMILESValidationResult(
            input_smiles=smiles_clean,
            is_valid=True,
            canonical_smiles=canonical_smiles,
            molecular_formula=formula,
            molecular_weight=round(mw, 4),
            logp=round(logp, 2),
            hbd=hbd,
            hba=hba,
            tpsa=round(tpsa, 2),
            heavy_atom_count=heavy_atoms,
        )
    except Exception as e:
        return SMILESValidationResult(
            input_smiles=smiles_clean,
            is_valid=False,
            error_message=f"Error calculating properties: {e}",
        )