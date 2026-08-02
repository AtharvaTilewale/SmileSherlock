"""PubChem REST API client for compound property lookup."""

import os
import time
import urllib.parse
from typing import Any, Dict, Optional, Union
import requests
from pydantic import BaseModel, Field

from smilesherlock.config import settings
from smilesherlock.logging_config import logger


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

    # FIX: Removed 'CID' from PROPERTIES. Requesting it explicitly causes a 400 Bad Request.
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
        self.rate_limit_delay = settings.rate_limit_delay

    def _make_request(
        self, url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute HTTP request with rate limiting and exponential backoff retries."""
        time.sleep(self.rate_limit_delay)

        for attempt in range(1, self.retries + 1):
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
                else:
                    logger.warning(
                        f"PubChem API status {response.status_code} (attempt {attempt}/{self.retries})"
                    )
            except requests.RequestException as e:
                logger.error(f"HTTP Request failed (attempt {attempt}/{self.retries}): {e}")

            if attempt < self.retries:
                time.sleep(attempt * 1.0)

        return None

    def lookup(
        self, query: Union[str, int], search_type: str = "auto"
    ) -> Optional[PubChemCompound]:
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

        # FIX: Using GET with urllib.parse.quote as per your working snippet
        encoded_query = urllib.parse.quote(query_str)
        prop_list = ",".join(self.PROPERTIES)
        
        url = f"{self.base_url}/compound/{search_type}/{encoded_query}/property/{prop_list}/JSON"
        json_data = self._make_request(url, method="GET")

        if not json_data or "PropertyTable" not in json_data:
            return None

        props = json_data["PropertyTable"]["Properties"][0]

        return PubChemCompound(
            cid=props.get("CID"),  # CID is safely extracted here even though it wasn't in the URL properties
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

    def download_3d_sdf(self, cid: int, output_dir: str = '3D_structures') -> str:
        """
        Download 3D SDF structure from PubChem for given CID.
        Implemented based on the provided working snippet.
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            url = f"{self.base_url}/compound/cid/{cid}/record/SDF/?record_type=3d"
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                output_file = os.path.join(output_dir, f"{cid}.sdf")
                with open(output_file, 'w') as f:
                    f.write(response.text)
                return 'Downloaded'
            elif response.status_code == 404:
                return 'Not Available'
            else:
                return f'Error {response.status_code}'
        except Exception as e:
            return f'Download Error: {str(e)}'