from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.molecule import Molecule
from app.models.protein import Protein
from app.models.analysis import Analysis
from app.schemas import DockingRequest
from app.services.adme_service import evaluate_adme
from app.services.swissadme_scraper import fetch_swissadme
from app.services.docking_service import perform_docking, generate_ligand_sdf
from app.services.vina_docking import run_vina_docking, is_vina_available
from app.services.rdkit_service import validate_smiles

router = APIRouter(prefix="/api/analysis", tags=["Analises"])


@router.get("/")
def list_analyses(user_id: str = "default", db: Session = Depends(get_db)):
    return db.query(Analysis).filter(Analysis.user_id == user_id).all()


@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")
    return analysis


@router.post("/validate/{molecule_id}")
def run_validation(molecule_id: int, user_id: str = "default", db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    result = validate_smiles(mol.smiles)

    analysis = Analysis(
        molecule_id=molecule_id,
        analysis_type="validation",
        results=result,
        status="completed",
        user_id=user_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {"analysis": analysis, "results": result}


@router.post("/adme/{molecule_id}")
def run_adme(
    molecule_id: int,
    user_id: str = "default",
    source: str = "swissadme",
    db: Session = Depends(get_db),
):
    """
    Avaliacao ADME.
    source: 'swissadme' (dados reais via scraping) ou 'local' (calculo RDKit)
    """
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    result = None
    if source == "swissadme":
        result = fetch_swissadme(mol.smiles)

    if not result or not result.get("success"):
        result = evaluate_adme(mol.smiles)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    analysis = Analysis(
        molecule_id=molecule_id,
        analysis_type="adme",
        results=result,
        status="completed",
        user_id=user_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {"analysis": analysis, "results": result}


@router.post("/docking")
def run_docking(data: DockingRequest, user_id: str = "default", db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == data.molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    protein = db.query(Protein).filter(Protein.id == data.protein_id).first()
    if not protein:
        raise HTTPException(status_code=404, detail="Proteina nao encontrada")

    # Tentar docking real com AutoDock Vina primeiro
    result = None
    ligand_sdf = None

    if protein.pdb_data and is_vina_available():
        vina_result = run_vina_docking(mol.smiles, protein.pdb_data, protein.name)
        if vina_result["success"]:
            result = vina_result
            ligand_sdf = vina_result.get("docked_ligand_sdf")
            # Adicionar campos compativeis com o formato anterior
            result["active_sites"] = [{
                "site_id": 1,
                "center": result["center"],
                "residues": [],
            }]
            result["interactions"] = []
            result["ligand_properties"] = {
                "smiles": mol.smiles,
                "modes": len(result.get("all_modes", [])),
            }

    # Fallback: simulacao por propriedades
    if result is None:
        result = perform_docking(mol.smiles, protein.name, protein.pdb_data)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        if result.get("active_sites"):
            site = result["active_sites"][0]
            center = site["center"]
            ligand_sdf = generate_ligand_sdf(mol.smiles, center["x"], center["y"], center["z"])

    analysis = Analysis(
        molecule_id=data.molecule_id,
        protein_id=data.protein_id,
        analysis_type="docking",
        results=result,
        binding_affinity=result["binding_affinity"],
        status="completed",
        user_id=user_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "analysis": analysis,
        "results": result,
        "viewer_data": {
            "protein_pdb": protein.pdb_data,
            "ligand_sdf": ligand_sdf,
            "active_site_residues": [
                r["number"] for r in result["active_sites"][0].get("residues", [])
            ] if result.get("active_sites") else [],
        },
    }


@router.post("/pipeline/{molecule_id}")
def run_full_pipeline(
    molecule_id: int,
    protein_id: Optional[int] = None,
    user_id: str = "default",
    db: Session = Depends(get_db),
):
    """Executa pipeline completo: Validacao -> ADME -> Docking."""
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    # 1. Validacao
    validation = validate_smiles(mol.smiles)
    db.add(Analysis(
        molecule_id=molecule_id,
        analysis_type="validation",
        results=validation,
        status="completed",
        user_id=user_id,
    ))

    # 2. ADME
    adme = evaluate_adme(mol.smiles)
    db.add(Analysis(
        molecule_id=molecule_id,
        analysis_type="adme",
        results=adme,
        status="completed",
        user_id=user_id,
    ))

    # 3. Docking (se proteina especificada)
    docking = None
    viewer_data = None
    if protein_id:
        protein = db.query(Protein).filter(Protein.id == protein_id).first()
        if protein:
            docking = perform_docking(mol.smiles, protein.name, protein.pdb_data)
            db.add(Analysis(
                molecule_id=molecule_id,
                protein_id=protein_id,
                analysis_type="docking",
                results=docking,
                binding_affinity=docking.get("binding_affinity"),
                status="completed",
                user_id=user_id,
            ))
            # Dados para visualizacao 3D
            ligand_sdf = None
            if docking.get("active_sites"):
                site = docking["active_sites"][0]
                center = site["center"]
                ligand_sdf = generate_ligand_sdf(mol.smiles, center["x"], center["y"], center["z"])
            viewer_data = {
                "protein_pdb": protein.pdb_data,
                "ligand_sdf": ligand_sdf,
                "active_site_residues": [
                    r["number"] for r in docking["active_sites"][0].get("residues", [])
                ] if docking.get("active_sites") else [],
            }

    db.commit()

    return {
        "molecule_id": molecule_id,
        "validation": validation,
        "adme": adme,
        "docking": docking,
        "viewer_data": viewer_data,
    }
