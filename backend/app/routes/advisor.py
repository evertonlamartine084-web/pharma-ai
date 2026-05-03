from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.molecule import Molecule
from app.models.analysis import Analysis
from app.services.ai_advisor import analyze_molecule

router = APIRouter(prefix="/api/advisor", tags=["Consultor IA"])


class QuestionRequest(BaseModel):
    molecule_id: int
    question: Optional[str] = None


@router.post("/analyze")
def analyze(data: QuestionRequest, user_id: str = "default", db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == data.molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    # Buscar ADME e docking existentes
    adme_analysis = db.query(Analysis).filter(
        Analysis.molecule_id == data.molecule_id,
        Analysis.analysis_type == "adme",
    ).order_by(Analysis.id.desc()).first()

    docking_analysis = db.query(Analysis).filter(
        Analysis.molecule_id == data.molecule_id,
        Analysis.analysis_type == "docking",
    ).order_by(Analysis.id.desc()).first()

    adme_data = adme_analysis.results if adme_analysis else None
    docking_data = docking_analysis.results if docking_analysis else None

    result = analyze_molecule(mol.smiles, adme_data, docking_data, data.question)
    result["molecule"] = {"id": mol.id, "name": mol.name, "smiles": mol.smiles}

    return result
