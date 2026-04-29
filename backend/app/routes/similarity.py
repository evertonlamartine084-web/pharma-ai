from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.molecule import Molecule
from app.services.similarity_service import tanimoto_similarity, find_similar, similarity_matrix

router = APIRouter(prefix="/api/similarity", tags=["Similaridade"])


class PairRequest(BaseModel):
    smiles1: str
    smiles2: str


@router.post("/pair")
def compare_pair(data: PairRequest):
    """Calcula similaridade Tanimoto entre duas moleculas."""
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
    """Encontra moleculas mais similares a uma molecula do banco."""
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

    return {
        "query": {"id": mol.id, "name": mol.name, "smiles": mol.smiles},
        "similar": results,
        "total_compared": len(candidates),
    }


@router.get("/matrix")
def get_similarity_matrix(
    user_id: str = "default",
    limit: int = Query(20, ge=2, le=50),
    db: Session = Depends(get_db),
):
    """Gera matriz de similaridade entre moleculas do banco."""
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
