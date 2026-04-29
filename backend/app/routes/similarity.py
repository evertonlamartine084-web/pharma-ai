from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.molecule import Molecule
from app.services.similarity_service import tanimoto_similarity, find_similar, similarity_matrix
from app.services.rdkit_service import validate_smiles

router = APIRouter(prefix="/api/similarity", tags=["Similaridade"])


def _get_pharma_props(smiles: str) -> dict:
    """Calcula propriedades farmacocineticas basicas para comparacao."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors, Crippen

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}

    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() in (7, 8, 9))
    rotatable = Lipinski.NumRotatableBonds(mol)
    lipinski_violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])

    gi_absorption = "High" if tpsa <= 131.6 and logp <= 5.88 else "Low"
    bbb = tpsa <= 79 and logp >= 0 and mw < 450
    solubility = 0.16 - 0.63 * logp - 0.0062 * mw + 0.066 * rotatable

    return {
        "mw": round(mw, 2),
        "logp": round(logp, 2),
        "tpsa": round(tpsa, 2),
        "hbd": hbd,
        "hba": hba,
        "rotatable": rotatable,
        "lipinski_violations": lipinski_violations,
        "gi_absorption": gi_absorption,
        "bbb_permeant": bbb,
        "log_s": round(solubility, 2),
    }


def _compare_props(ref: dict, candidate: dict) -> list:
    """Compara propriedades e gera lista de melhorias/pioras."""
    changes = []

    # MW: mais proximo de 350 e melhor
    if ref.get("mw") and candidate.get("mw"):
        ref_dist = abs(ref["mw"] - 350)
        cand_dist = abs(candidate["mw"] - 350)
        if cand_dist < ref_dist - 10:
            changes.append({"prop": "MW", "direction": "up", "detail": f'{candidate["mw"]} (ref: {ref["mw"]})', "reason": "Mais proximo do ideal (~350)"})
        elif cand_dist > ref_dist + 10:
            changes.append({"prop": "MW", "direction": "down", "detail": f'{candidate["mw"]} (ref: {ref["mw"]})', "reason": "Mais distante do ideal (~350)"})

    # LogP: ideal entre 1-3
    if ref.get("logp") is not None and candidate.get("logp") is not None:
        ref_ideal = abs(ref["logp"] - 2)
        cand_ideal = abs(candidate["logp"] - 2)
        if cand_ideal < ref_ideal - 0.3:
            changes.append({"prop": "LogP", "direction": "up", "detail": f'{candidate["logp"]} (ref: {ref["logp"]})', "reason": "Lipofilicidade mais equilibrada (ideal ~2)"})
        elif cand_ideal > ref_ideal + 0.3:
            changes.append({"prop": "LogP", "direction": "down", "detail": f'{candidate["logp"]} (ref: {ref["logp"]})', "reason": "Lipofilicidade menos equilibrada"})

    # TPSA: ideal 60-120
    if ref.get("tpsa") and candidate.get("tpsa"):
        if candidate["tpsa"] < ref["tpsa"] and ref["tpsa"] > 120:
            changes.append({"prop": "TPSA", "direction": "up", "detail": f'{candidate["tpsa"]} (ref: {ref["tpsa"]})', "reason": "Melhor absorcao GI (TPSA reduzido)"})
        elif candidate["tpsa"] > ref["tpsa"] and ref["tpsa"] < 60:
            changes.append({"prop": "TPSA", "direction": "up", "detail": f'{candidate["tpsa"]} (ref: {ref["tpsa"]})', "reason": "Melhor solubilidade (TPSA aumentado)"})

    # Lipinski: menos violacoes e melhor
    if ref.get("lipinski_violations") is not None and candidate.get("lipinski_violations") is not None:
        if candidate["lipinski_violations"] < ref["lipinski_violations"]:
            changes.append({"prop": "Lipinski", "direction": "up", "detail": f'{candidate["lipinski_violations"]} violacoes (ref: {ref["lipinski_violations"]})', "reason": "Melhor drug-likeness"})
        elif candidate["lipinski_violations"] > ref["lipinski_violations"]:
            changes.append({"prop": "Lipinski", "direction": "down", "detail": f'{candidate["lipinski_violations"]} violacoes (ref: {ref["lipinski_violations"]})', "reason": "Pior drug-likeness"})

    # GI absorption
    if ref.get("gi_absorption") and candidate.get("gi_absorption"):
        if candidate["gi_absorption"] == "High" and ref["gi_absorption"] == "Low":
            changes.append({"prop": "Absorcao GI", "direction": "up", "detail": "High (ref: Low)", "reason": "Melhor absorcao gastrointestinal"})
        elif candidate["gi_absorption"] == "Low" and ref["gi_absorption"] == "High":
            changes.append({"prop": "Absorcao GI", "direction": "down", "detail": "Low (ref: High)", "reason": "Pior absorcao gastrointestinal"})

    # BBB
    if ref.get("bbb_permeant") is not None and candidate.get("bbb_permeant") is not None:
        if candidate["bbb_permeant"] and not ref["bbb_permeant"]:
            changes.append({"prop": "BBB", "direction": "up", "detail": "Permeavel (ref: Nao)", "reason": "Agora atravessa barreira hematoencefalica"})
        elif not candidate["bbb_permeant"] and ref["bbb_permeant"]:
            changes.append({"prop": "BBB", "direction": "down", "detail": "Nao permeavel (ref: Sim)", "reason": "Nao atravessa mais a BBB"})

    # Solubilidade
    if ref.get("log_s") is not None and candidate.get("log_s") is not None:
        if candidate["log_s"] > ref["log_s"] + 0.3:
            changes.append({"prop": "Solubilidade", "direction": "up", "detail": f'LogS {candidate["log_s"]} (ref: {ref["log_s"]})', "reason": "Melhor solubilidade aquosa"})
        elif candidate["log_s"] < ref["log_s"] - 0.3:
            changes.append({"prop": "Solubilidade", "direction": "down", "detail": f'LogS {candidate["log_s"]} (ref: {ref["log_s"]})', "reason": "Pior solubilidade aquosa"})

    # HBD: menos e geralmente melhor para permeabilidade
    if ref.get("hbd") is not None and candidate.get("hbd") is not None:
        if candidate["hbd"] < ref["hbd"]:
            changes.append({"prop": "H-Bond Donors", "direction": "up", "detail": f'{candidate["hbd"]} (ref: {ref["hbd"]})', "reason": "Melhor permeabilidade de membrana"})
        elif candidate["hbd"] > ref["hbd"] and candidate["hbd"] > 5:
            changes.append({"prop": "H-Bond Donors", "direction": "down", "detail": f'{candidate["hbd"]} (ref: {ref["hbd"]})', "reason": "Pode reduzir permeabilidade"})

    # Rotatable bonds: menos e melhor para biodisponibilidade oral
    if ref.get("rotatable") is not None and candidate.get("rotatable") is not None:
        if candidate["rotatable"] < ref["rotatable"] and ref["rotatable"] > 7:
            changes.append({"prop": "Flex. Molecular", "direction": "up", "detail": f'{candidate["rotatable"]} rot. bonds (ref: {ref["rotatable"]})', "reason": "Menor flexibilidade, melhor biodisponibilidade oral"})

    # Se nao houve mudancas significativas
    if not changes:
        changes.append({"prop": "Geral", "direction": "neutral", "detail": "Propriedades similares", "reason": "Sem mudancas significativas na farmacocinetica"})

    return changes


class PairRequest(BaseModel):
    smiles1: str
    smiles2: str


@router.post("/pair")
def compare_pair(data: PairRequest):
    result = tanimoto_similarity(data.smiles1, data.smiles2)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/find/{molecule_id}")
def find_similar_molecules(
    molecule_id: int,
    top_n: int = Query(10, ge=1, le=50),
    user_id: str = "default",
    db: Session = Depends(get_db),
):
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    all_mols = db.query(Molecule).filter(
        Molecule.user_id == user_id,
        Molecule.id != molecule_id,
        Molecule.is_valid == True,
    ).all()

    candidates = [{"id": m.id, "name": m.name, "smiles": m.smiles} for m in all_mols]
    results = find_similar(mol.smiles, candidates, top_n)

    # Propriedades da molecula de referencia
    ref_props = _get_pharma_props(mol.smiles)

    # Adicionar propriedades e comparacao a cada similar
    for r in results:
        r["props"] = _get_pharma_props(r["smiles"])
        r["changes"] = _compare_props(ref_props, r["props"])

    return {
        "query": {"id": mol.id, "name": mol.name, "smiles": mol.smiles, "props": ref_props},
        "similar": results,
        "total_compared": len(candidates),
    }


@router.get("/matrix")
def get_similarity_matrix(
    user_id: str = "default",
    limit: int = Query(20, ge=2, le=50),
    db: Session = Depends(get_db),
):
    mols = db.query(Molecule).filter(
        Molecule.user_id == user_id,
        Molecule.is_valid == True,
    ).limit(limit).all()

    if len(mols) < 2:
        raise HTTPException(status_code=400, detail="Minimo 2 moleculas validas necessarias")

    smiles_list = [m.smiles for m in mols]
    names = [m.name for m in mols]
    ids = [m.id for m in mols]

    result = similarity_matrix(smiles_list)
    result["names"] = names
    result["ids"] = ids

    return result
