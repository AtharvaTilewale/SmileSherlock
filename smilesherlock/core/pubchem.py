"""PubChem REST API client for compound property lookup and structure downloads."""

import os
import time
import threading
import urllib.parse
from typing import Any, Dict, Optional, Union
import requests
from pydantic import BaseModel, Field

from smilesherlock.config import settings
from smilesherlock.logging_config import logger

try:
    from rdkit import Chem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


class RateLimiter:
    """Thread-safe rate limiter to respect PubChem API constraints."""
    def __init__(self, delay: float):
        self.delay = delay
        self.lock = threading.Lock()
        self.last_call = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
            self.last_call = time.time()

# Global rate limiter shared across all threads
api_limiter = RateLimiter(settings.rate_limit_delay)


class PubChemCompound(BaseModel):
    """Pydantic model representing PubChem compound metadata."""
    cid: Optional[int] = Field(None, description="PubChem Compound ID")
    input_query: Optional[str] = Field(None, description="Original query string")
    smiles: Optional[str] = Field(None, description="SMILES string")
    canonical_smiles: Optional[str] = Field(None, description="Canonical SMILES")
    iupac_name: Optional[str] = Field(None, description="IUPAC Name")
    molecular_formula: Optional[str] = Field(None, description="Molecular Formula")
    molecular_weight: Optional[float] = Field(None, description="Molecular Weight (g/mol)")
    inchi: Optional[str] = Field(None, description="InChI string")
    inchikey: Optional[str] = Field(None, description="InChIKey")
    xlogp: Optional[float] = Field(None, description="XLogP calculated value")
    exact_mass: Optional[float] = Field(None, description="Exact Mass")
    charge: Optional[int] = Field(None, description="Formal Charge")
    hbond_donor_count: Optional[int] = Field(None, description="H-Bond Donor Count")
    hbond_acceptor_count: Optional[int] = Field(None, description="H-Bond Acceptor Count")


class PubChemClient:
    """Client for interacting with the PubChem PUG REST API."""

    PROPERTIES = [
        "IUPACName",
        "MolecularFormula",
        "MolecularWeight",
        "CanonicalSMILES",
        "InChI",
        "InChIKey",
        "XLogP",
        "ExactMass",
        "Charge",
        "HBondDonorCount",
        "HBondAcceptorCount",
    ]

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or settings.pubchem_base_url).rstrip("/")
        self.timeout = timeout or settings.pubchem_timeout
        self.retries = settings.pubchem_retries

    def _make_request(
        self, url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute HTTP request with strict thread-safe rate limiting and exponential backoff."""
        
        for attempt in range(1, self.retries + 1):
            api_limiter.wait()  # Thread-safe wait
            
            try:
                if method.upper() == "POST":
                    response = requests.post(url, data=data, timeout=self.timeout)
                else:
                    response = requests.get(url, timeout=self.timeout)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.debug(f"PubChem resource not found: {url}")
                    return None
                elif response.status_code == 503:
                    # PubChem is telling us to slow down explicitly
                    logger.warning("PubChem 503 Server Busy. Extending backoff.")
                    time.sleep(attempt * 2.0)
                else:
                    logger.warning(f"PubChem API status {response.status_code} (attempt {attempt}/{self.retries})")
            except requests.RequestException as e:
                logger.error(f"HTTP Request failed (attempt {attempt}/{self.retries}): {e}")

            if attempt < self.retries:
                time.sleep(attempt * 1.0)

        return None

    def lookup(self, query: Union[str, int], search_type: str = "auto") -> Optional[PubChemCompound]:
        """Lookup compound metadata from PubChem."""
        query_str = str(query).strip()
        if not query_str:
            return None

        if search_type == "auto":
            if query_str.isdigit():
                search_type = "cid"
            elif query_str.startswith("InChI="):
                search_type = "inchi"
            elif len(query_str) == 27 and query_str[14] == "-" and query_str[25] == "-":
                search_type = "inchikey"
            elif any(c in query_str for c in ["=", "#", "(", ")", "[", "]", "c", "C", "n", "N"]):
                search_type = "smiles"
            else:
                search_type = "name"

        encoded_query = urllib.parse.quote(query_str)
        prop_list = ",".join(self.PROPERTIES)
        
        url = f"{self.base_url}/compound/{search_type}/{encoded_query}/property/{prop_list}/JSON"
        json_data = self._make_request(url, method="GET")

        if not json_data or "PropertyTable" not in json_data:
            return None

        props = json_data["PropertyTable"]["Properties"][0]

        return PubChemCompound(
            cid=props.get("CID"),
            input_query=query_str,
            smiles=props.get("CanonicalSMILES"),
            canonical_smiles=props.get("CanonicalSMILES"),
            iupac_name=props.get("IUPACName"),
            molecular_formula=props.get("MolecularFormula"),
            molecular_weight=float(props["MolecularWeight"]) if props.get("MolecularWeight") is not None else None,
            inchi=props.get("InChI"),
            inchikey=props.get("InChIKey"),
            xlogp=float(props["XLogP"]) if props.get("XLogP") is not None else None,
            exact_mass=float(props["ExactMass"]) if props.get("ExactMass") is not None else None,
            charge=int(props["Charge"]) if props.get("Charge") is not None else None,
            hbond_donor_count=int(props["HBondDonorCount"]) if props.get("HBondDonorCount") is not None else None,
            hbond_acceptor_count=int(props["HBondAcceptorCount"]) if props.get("HBondAcceptorCount") is not None else None,
        )

    def download_structure(self, cid: int, format: str = "sdf", dimension: str = "3d", output_dir: str = "structures", force: bool = False) -> str:
        """Download 2D/3D structure from PubChem safely across threads."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            fmt = format.lower().strip()
            dim = dimension.lower().strip()
            output_file = os.path.join(output_dir, f"{cid}_{dim}.{fmt}")

            # Resume logic: skip if file exists and has content
            if not force and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return 'Skipped (Already exists)'

            api_limiter.wait()  # Thread-safe rate limiting

            if fmt == "png":
                url = f"{self.base_url}/compound/cid/{cid}/PNG?record_type={dim}&image_size=large"
                response = requests.get(url, timeout=self.timeout)
            else:
                url = f"{self.base_url}/compound/cid/{cid}/record/SDF/?record_type={dim}"
                response = requests.get(url, timeout=self.timeout)

            if response.status_code == 200:
                if fmt in ["sdf", "png"]:
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                elif fmt in ["mol", "pdb"]:
                    if not RDKIT_AVAILABLE:
                        return "Error: RDKit is required for MOL or PDB conversion"
                    
                    temp_sdf = os.path.join(output_dir, f"temp_{cid}_{threading.get_ident()}.sdf")
                    with open(temp_sdf, 'wb') as f:
                        f.write(response.content)
                    
                    supplier = Chem.SDMolSupplier(temp_sdf)
                    mol = next(supplier)
                    if mol is None:
                        os.remove(temp_sdf)
                        return "Error: Invalid SDF retrieved from PubChem"
                    
                    if fmt == "mol":
                        Chem.MolToMolFile(mol, output_file)
                    elif fmt == "pdb":
                        Chem.MolToPDBFile(mol, output_file)
                        
                    os.remove(temp_sdf)
                else:
                    return f"Error: Unsupported format '{fmt}'"

                return 'Downloaded'
            elif response.status_code == 404:
                return 'Not Available'
            else:
                return f'Error {response.status_code}'
        except Exception as e:
            return f'Download Error: {str(e)}'