from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.protein import Protein
from app.schemas import ProteinSequenceInput, UniprotInput
from app.services.alphafold_service import (
    fetch_structure_by_uniprot,
    parse_pdb_content,
    LEISHMANIA_PROTEINS,
)

router = APIRouter(prefix="/api/proteins", tags=["Proteinas"])


@router.get("/")
def list_proteins(user_id: str = "default", db: Session = Depends(get_db)):
    return db.query(Protein).filter(Protein.user_id == user_id).all()


@router.get("/{protein_id}")
def get_protein(protein_id: int, db: Session = Depends(get_db)):
    protein = db.query(Protein).filter(Protein.id == protein_id).first()
    if not protein:
        raise HTTPException(status_code=404, detail="Proteina nao encontrada")
    return protein


@router.post("/upload-pdb")
async def upload_pdb(
    name: str = "Uploaded Protein",
    organism: str = "Leishmania",
    user_id: str = "default",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    pdb_text = content.decode("utf-8")
    info = parse_pdb_content(pdb_text)

    protein = Protein(
        name=name,
        organism=organism,
        pdb_data=pdb_text,
        source="upload",
        user_id=user_id,
    )
    db.add(protein)
    db.commit()
    db.refresh(protein)

    return {"protein": protein, "pdb_info": info}


@router.post("/sequence")
def add_sequence(data: ProteinSequenceInput, user_id: str = "default", db: Session = Depends(get_db)):
    protein = Protein(
        name=data.name,
        organism=data.organism,
        sequence=data.sequence,
        source="manual",
        user_id=user_id,
    )
    db.add(protein)
    db.commit()
    db.refresh(protein)
    return protein


@router.post("/fetch-pdb")
def fetch_from_rcsb(pdb_id: str, name: str = "", user_id: str = "default", db: Session = Depends(get_db)):
    """Busca estrutura molecular do RCSB Protein Data Bank por codigo PDB (ex: 3EDJ, 1A2B)."""
    import requests as req

    pdb_id = pdb_id.strip().upper()
    if len(pdb_id) != 4:
        raise HTTPException(status_code=400, detail="Codigo PDB deve ter 4 caracteres (ex: 3EDJ)")

    # Buscar PDB do RCSB
    pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        resp = req.get(pdb_url, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Estrutura {pdb_id} nao encontrada no RCSB PDB")
    except req.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar RCSB: {e}")

    pdb_data = resp.text

    # Extrair info do PDB
    info = parse_pdb_content(pdb_data)
    organism = ""
    mol_type = "Proteina"
    for line in pdb_data.split("\n"):
        if line.startswith("SOURCE") and "ORGANISM_SCIENTIFIC" in line:
            organism = line.split(":")[-1].strip().rstrip(";")
        if line.startswith("HEADER"):
            mol_type = line[10:50].strip()

    protein = Protein(
        name=name or f"{pdb_id} - {mol_type}",
        organism=organism,
        pdb_data=pdb_data,
        source="rcsb_pdb",
        user_id=user_id,
    )
    db.add(protein)
    db.commit()
    db.refresh(protein)

    return {
        "protein": protein,
        "pdb_info": info,
        "pdb_id": pdb_id,
        "molecule_type": mol_type,
    }


@router.post("/alphafold")
def fetch_alphafold(data: UniprotInput, user_id: str = "default", db: Session = Depends(get_db)):
    result = fetch_structure_by_uniprot(data.uniprot_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    name = data.name or f"AlphaFold-{data.uniprot_id}"
    protein = Protein(
        name=name,
        organism=result.get("organism", ""),
        pdb_data=result["pdb_data"],
        source="alphafold",
        user_id=user_id,
    )
    db.add(protein)
    db.commit()
    db.refresh(protein)

    return {"protein": protein, "confidence": result.get("confidence")}


@router.post("/seed-leishmania")
def seed_leishmania_proteins(user_id: str = "default", db: Session = Depends(get_db)):
    """Popula o banco com proteinas conhecidas de Leishmania."""
    added = []
    for pdata in LEISHMANIA_PROTEINS:
        existing = db.query(Protein).filter(
            Protein.name == pdata["name"],
            Protein.user_id == user_id,
        ).first()
        if existing:
            continue

        protein = Protein(
            name=pdata["name"],
            organism=pdata["organism"],
            sequence=pdata["sequence"],
            source="database",
            user_id=user_id,
        )
        db.add(protein)
        db.commit()
        db.refresh(protein)
        added.append(protein)

    return {"added": len(added), "proteins": added}


@router.get("/{protein_id}/pdb")
def get_pdb_data(protein_id: int, db: Session = Depends(get_db)):
    protein = db.query(Protein).filter(Protein.id == protein_id).first()
    if not protein:
        raise HTTPException(status_code=404, detail="Proteina nao encontrada")
    if not protein.pdb_data:
        raise HTTPException(status_code=404, detail="Dados PDB nao disponiveis")
    return {"pdb_data": protein.pdb_data}
