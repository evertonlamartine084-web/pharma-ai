from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski


def validate_smiles(smiles: str) -> dict:
    """Valida uma molecula SMILES e retorna propriedades quimicas."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"valid": False, "error": "SMILES invalido"}

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable_bonds = Lipinski.NumRotatableBonds(mol)

    # Regra de Lipinski (Rule of Five)
    lipinski_violations = sum([
        mw > 500,
        logp > 5,
        hbd > 5,
        hba > 10,
    ])
    lipinski_pass = lipinski_violations <= 1

    return {
        "valid": True,
        "molecular_weight": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 2),
        "rotatable_bonds": rotatable_bonds,
        "lipinski_violations": lipinski_violations,
        "lipinski_pass": lipinski_pass,
        "canonical_smiles": Chem.MolToSmiles(mol),
    }


def batch_validate(smiles_list: list[str]) -> list[dict]:
    """Valida uma lista de SMILES."""
    return [validate_smiles(s) for s in smiles_list]
