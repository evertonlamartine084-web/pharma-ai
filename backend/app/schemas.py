from typing import List, Optional

from pydantic import BaseModel


class SMILESInput(BaseModel):
    name: str
    smiles: str
    target_protein_id: Optional[int] = None


class SMILESBatchInput(BaseModel):
    molecules: List[SMILESInput]


class GenerateMoleculesRequest(BaseModel):
    seed_smiles: str
    n_molecules: int = 10
    target_protein_id: Optional[int] = None


class ProteinSequenceInput(BaseModel):
    name: str
    sequence: str
    organism: str = "Leishmania"


class UniprotInput(BaseModel):
    uniprot_id: str
    name: str = ""


class DockingRequest(BaseModel):
    molecule_id: int
    protein_id: int


class ExportRequest(BaseModel):
    format: str = "json"
    user_id: str = "default"
