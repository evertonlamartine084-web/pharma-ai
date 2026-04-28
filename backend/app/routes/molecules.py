import csv
import io
import json

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.molecule import Molecule
from app.schemas import SMILESInput, SMILESBatchInput, GenerateMoleculesRequest, ExportRequest
from app.services.rdkit_service import validate_smiles
from app.services.molecule_generator import generate_molecules

router = APIRouter(prefix="/api/molecules", tags=["Moleculas"])

# Moleculas conhecidas para Leishmaniose (banco inicial)
SEED_MOLECULES = [
    {"name": "Miltefosina", "smiles": "CCCCCCCCCCCCCCCCOP(=O)([O-])OCC[N+](C)(C)C"},
    {"name": "Anfotericina B", "smiles": "OC1C=CC=CC=CC=CC=CC=CC=CC(CC2OC(O)(CC(O)CC(O)CC(O)CC(O)CC(O)CC(O)CC3OC(C)(C)C(O)C(C)O3)CC(O)C2C(O)=O)OC(C)C(O)C(N)C1O"},
    {"name": "Paromomicina", "smiles": "NC1C(O)C(O)C(CN)OC1OC1C(O)C(OC2OC(CO)C(O)C(N)C2O)C(N)CC1OC1OC(CO)C(O)C(O)C1N"},
    {"name": "Sitamaquina", "smiles": "COc1cc(NC(C)CCCN(CC)CC)c2ncccc2c1"},
    {"name": "Pentamidina", "smiles": "NC(=N)c1ccc(OCCCCCOc2ccc(C(=N)N)cc2)cc1"},
]


@router.get("/")
def list_molecules(user_id: str = "default", db: Session = Depends(get_db)):
    return db.query(Molecule).filter(Molecule.user_id == user_id).all()


@router.get("/{molecule_id}")
def get_molecule(molecule_id: int, db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")
    return mol


@router.post("/add")
def add_smiles(data: SMILESInput, user_id: str = "default", db: Session = Depends(get_db)):
    validation = validate_smiles(data.smiles)

    mol = Molecule(
        name=data.name,
        smiles=data.smiles,
        target_protein_id=data.target_protein_id,
        source="manual",
        is_valid=validation["valid"],
        molecular_weight=validation.get("molecular_weight"),
        logp=validation.get("logp"),
        hbd=validation.get("hbd"),
        hba=validation.get("hba"),
        lipinski_pass=validation.get("lipinski_pass"),
        user_id=user_id,
    )
    db.add(mol)
    db.commit()
    db.refresh(mol)

    return {"molecule": mol, "validation": validation}


@router.post("/batch")
def add_batch(data: SMILESBatchInput, user_id: str = "default", db: Session = Depends(get_db)):
    results = []
    for item in data.molecules:
        validation = validate_smiles(item.smiles)
        mol = Molecule(
            name=item.name,
            smiles=item.smiles,
            target_protein_id=item.target_protein_id,
            source="manual",
            is_valid=validation["valid"],
            molecular_weight=validation.get("molecular_weight"),
            logp=validation.get("logp"),
            hbd=validation.get("hbd"),
            hba=validation.get("hba"),
            lipinski_pass=validation.get("lipinski_pass"),
            user_id=user_id,
        )
        db.add(mol)
        results.append({"molecule_name": item.name, "validation": validation})

    db.commit()
    return {"count": len(results), "results": results}


@router.post("/upload-csv")
async def upload_csv(
    user_id: str = "default",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    results = []
    for row in reader:
        name = row.get("name", row.get("nome", ""))
        smiles = row.get("smiles", row.get("SMILES", ""))
        if not smiles:
            continue

        validation = validate_smiles(smiles)
        mol = Molecule(
            name=name or smiles[:30],
            smiles=smiles,
            source="csv",
            is_valid=validation["valid"],
            molecular_weight=validation.get("molecular_weight"),
            logp=validation.get("logp"),
            hbd=validation.get("hbd"),
            hba=validation.get("hba"),
            lipinski_pass=validation.get("lipinski_pass"),
            user_id=user_id,
        )
        db.add(mol)
        results.append({"name": name, "valid": validation["valid"]})

    db.commit()
    return {"count": len(results), "results": results}


@router.post("/generate")
def generate(data: GenerateMoleculesRequest, user_id: str = "default", db: Session = Depends(get_db)):
    generated = generate_molecules(data.seed_smiles, data.n_molecules)

    saved = []
    for i, gen in enumerate(generated):
        validation = validate_smiles(gen["smiles"])
        mol = Molecule(
            name=f"GEN-{i+1}-{gen['strategy']}",
            smiles=gen["smiles"],
            target_protein_id=data.target_protein_id,
            source="generated",
            is_valid=validation["valid"],
            molecular_weight=validation.get("molecular_weight"),
            logp=validation.get("logp"),
            hbd=validation.get("hbd"),
            hba=validation.get("hba"),
            lipinski_pass=validation.get("lipinski_pass"),
            user_id=user_id,
        )
        db.add(mol)
        saved.append({**gen, "validation": validation})

    db.commit()
    return {"count": len(saved), "molecules": saved}


@router.post("/validate/{molecule_id}")
def validate_molecule(molecule_id: int, db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    validation = validate_smiles(mol.smiles)
    mol.is_valid = validation["valid"]
    mol.molecular_weight = validation.get("molecular_weight")
    mol.logp = validation.get("logp")
    mol.hbd = validation.get("hbd")
    mol.hba = validation.get("hba")
    mol.lipinski_pass = validation.get("lipinski_pass")
    db.commit()

    return {"molecule_id": molecule_id, "validation": validation}


@router.post("/seed")
def seed_molecules(user_id: str = "default", db: Session = Depends(get_db)):
    """Popula banco com moleculas conhecidas para Leishmaniose."""
    added = []
    for sdata in SEED_MOLECULES:
        existing = db.query(Molecule).filter(
            Molecule.name == sdata["name"],
            Molecule.user_id == user_id,
        ).first()
        if existing:
            continue

        validation = validate_smiles(sdata["smiles"])
        mol = Molecule(
            name=sdata["name"],
            smiles=sdata["smiles"],
            source="database",
            is_valid=validation["valid"],
            molecular_weight=validation.get("molecular_weight"),
            logp=validation.get("logp"),
            hbd=validation.get("hbd"),
            hba=validation.get("hba"),
            lipinski_pass=validation.get("lipinski_pass"),
            user_id=user_id,
        )
        db.add(mol)
        db.commit()
        db.refresh(mol)
        added.append(mol)

    return {"added": len(added), "molecules": added}


@router.post("/export")
def export_molecules(data: ExportRequest, db: Session = Depends(get_db)):
    molecules = db.query(Molecule).filter(Molecule.user_id == data.user_id).all()

    rows = [
        {
            "id": m.id,
            "name": m.name,
            "smiles": m.smiles,
            "is_valid": m.is_valid,
            "molecular_weight": m.molecular_weight,
            "logp": m.logp,
            "lipinski_pass": m.lipinski_pass,
            "source": m.source,
        }
        for m in molecules
    ]

    if data.format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=molecules.csv"},
        )

    return rows
