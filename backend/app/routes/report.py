"""Endpoint para gerar relatorio PDF de uma molecula candidata."""

import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.database import get_db
from app.models.molecule import Molecule
from app.models.analysis import Analysis
from app.services.rdkit_service import validate_smiles
from app.services.adme_service import evaluate_adme

router = APIRouter(prefix="/api/report", tags=["Relatorio"])

CYAN = HexColor('#22D3EE')
NAVY = HexColor('#0B132B')
GRAY = HexColor('#64748b')
WHITE = HexColor('#ffffff')
GREEN = HexColor('#A3E635')
RED = HexColor('#ef4444')


@router.get("/molecule/{molecule_id}")
def generate_report(molecule_id: int, user_id: str = "default", db: Session = Depends(get_db)):
    mol = db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if not mol:
        raise HTTPException(status_code=404, detail="Molecula nao encontrada")

    # Buscar analises
    analyses = db.query(Analysis).filter(Analysis.molecule_id == molecule_id).all()
    adme_analysis = next((a for a in analyses if a.analysis_type == "adme"), None)
    docking_analysis = next((a for a in analyses if a.analysis_type == "docking"), None)

    # Validacao
    validation = validate_smiles(mol.smiles)

    # ADME local se nao tiver
    adme = adme_analysis.results if adme_analysis else evaluate_adme(mol.smiles)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=18, textColor=CYAN, spaceAfter=5)
    subtitle_style = ParagraphStyle('Subtitle2', parent=styles['Normal'], fontSize=10, textColor=GRAY, spaceAfter=15)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13, textColor=CYAN, spaceBefore=15, spaceAfter=8)
    normal = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9, textColor=HexColor('#334155'))
    small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=GRAY)

    elements = []

    # Header
    elements.append(Paragraph("PharmaAI - Relatorio de Molecula Candidata", title_style))
    elements.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | ID: {mol.id}", subtitle_style))

    # Info basica
    elements.append(Paragraph("Identificacao", section_style))
    info_data = [
        ["Nome", mol.name],
        ["SMILES", mol.smiles[:80] + ("..." if len(mol.smiles) > 80 else "")],
        ["Fonte", mol.source],
        ["Valido", "Sim" if mol.is_valid else "Nao"],
    ]
    t = Table(info_data, colWidths=[40*mm, 130*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), CYAN),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#334155')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ]))
    elements.append(t)

    # Propriedades fisico-quimicas
    elements.append(Paragraph("Propriedades Fisico-quimicas", section_style))
    props = validation if validation.get("valid") else {}
    phys_data = [
        ["Peso Molecular", f"{props.get('molecular_weight', '-')} g/mol"],
        ["LogP", str(props.get('logp', '-'))],
        ["TPSA", f"{props.get('tpsa', '-')} A2"],
        ["HBD", str(props.get('hbd', '-'))],
        ["HBA", str(props.get('hba', '-'))],
        ["Rotatable Bonds", str(props.get('rotatable_bonds', '-'))],
        ["Lipinski", "PASS" if props.get('lipinski_pass') else "FAIL"],
        ["Violacoes Lipinski", str(props.get('lipinski_violations', '-'))],
    ]
    t = Table(phys_data, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor('#e2e8f0')),
    ]))
    elements.append(t)

    # ADME
    if adme and adme.get("success", True):
        elements.append(Paragraph("Avaliacao ADME", section_style))
        source = adme.get("source", "Local (RDKit)")
        elements.append(Paragraph(f"Fonte: {source}", small))

        pc = adme.get("physicochemical", {})
        lp = adme.get("lipophilicity", {})
        sol = adme.get("solubility", {})
        pk = adme.get("pharmacokinetics", {})
        dl = adme.get("druglikeness", {})
        mc = adme.get("medicinal_chemistry", {})

        adme_data = [
            ["Formula", pc.get("formula", "-")],
            ["Consensus LogP", str(lp.get("consensus_logp", "-"))],
            ["Log S (ESOL)", str(sol.get("log_s_esol", "-"))],
            ["Classe Solubilidade", sol.get("class_esol", sol.get("class", "-"))],
            ["Absorcao GI", pk.get("gi_absorption", "-")],
            ["BBB Permeavel", "Sim" if pk.get("bbb_permeant") else "Nao"],
            ["P-gp Substrato", "Sim" if pk.get("pgp_substrate") else "Nao"],
            ["CYP2D6 Inibidor", "Sim" if pk.get("cyp2d6_inhibitor") else "Nao"],
            ["CYP3A4 Inibidor", "Sim" if pk.get("cyp3a4_inhibitor") else "Nao"],
            ["Log Kp (pele)", f"{pk.get('log_kp_skin', '-')} cm/s"],
            ["Lipinski", dl.get("lipinski", "-")],
            ["Ghose", dl.get("ghose", "-")],
            ["Veber", dl.get("veber", "-")],
            ["Bioavailability", str(dl.get("bioavailability_score", "-"))],
            ["PAINS", mc.get("pains_alerts", "-")],
            ["Brenk", mc.get("brenk_alerts", "-")],
            ["Leadlikeness", mc.get("leadlikeness", "-")],
            ["Synth. Accessibility", str(mc.get("synthetic_accessibility", "-"))],
        ]
        t = Table(adme_data, colWidths=[50*mm, 120*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor('#e2e8f0')),
        ]))
        elements.append(t)

    # Docking
    if docking_analysis and docking_analysis.results:
        elements.append(Paragraph("Docking Molecular", section_style))
        dr = docking_analysis.results
        dock_data = [
            ["Metodo", dr.get("method", "Simulacao")],
            ["Binding Affinity", f"{dr.get('binding_affinity', '-')} kcal/mol"],
            ["Classificacao", dr.get("classification", "-")],
            ["Proteina", dr.get("protein", "-")],
        ]
        modes = dr.get("all_modes", [])
        if modes:
            for m in modes[:5]:
                dock_data.append([f"Modo {m['mode']}", f"{m['affinity']} kcal/mol (RMSD: {m.get('rmsd_lb', '-')}/{m.get('rmsd_ub', '-')})"])

        t = Table(dock_data, colWidths=[50*mm, 120*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor('#e2e8f0')),
        ]))
        elements.append(t)

    # Footer
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("PharmaAI - Plataforma de IA para Descoberta de Farmacos", small))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PharmaAI_Molecula_{mol.id}_{mol.name}.pdf"},
    )
