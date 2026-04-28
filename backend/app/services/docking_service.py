from __future__ import annotations

"""
Servico de docking molecular (simulacao de interacao proteina-ligante).

UCSF Chimera requer instalacao local e nao possui API REST.
Este modulo implementa uma simulacao funcional de docking baseada em
propriedades moleculares calculadas, util para prototipagem e ensino.

Para producao, substituir por integracao real com AutoDock Vina ou
UCSF ChimeraX via linha de comando.
"""

import hashlib
import math
import random

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors


def perform_docking(smiles: str, protein_name: str, pdb_data: str | None = None) -> dict:
    """
    Simula docking molecular entre ligante (SMILES) e proteina.

    O score de binding affinity e estimado com base em propriedades
    moleculares do ligante e caracteristicas da proteina, combinando:
    - Contribuicao hidrofobica (logP)
    - Complementaridade de tamanho (peso molecular)
    - Capacidade de formar ligacoes de hidrogenio
    - Flexibilidade molecular
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"success": False, "error": "SMILES invalido"}

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)

    # Seed deterministica baseada no par ligante-proteina
    seed_str = f"{Chem.MolToSmiles(mol)}:{protein_name}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Calculo do binding affinity estimado (kcal/mol)
    # Valores tipicos: -3 a -12 kcal/mol (mais negativo = melhor)
    base_score = -5.0

    # Contribuicao hidrofobica (logP entre 1-3 e ideal)
    hydrophobic_contrib = -0.3 * max(0, min(logp, 5)) + 0.1 * max(0, logp - 5)

    # Ligacoes de hidrogenio melhoram a afinidade
    hbond_contrib = -0.2 * min(hbd + hba, 8)

    # Penalidade por flexibilidade excessiva
    flexibility_penalty = 0.1 * max(0, rotatable - 5)

    # Bonus por aneis aromaticos (stacking)
    aromatic_bonus = -0.3 * min(aromatic_rings, 3)

    # Penalidade por tamanho (muito grande ou muito pequeno)
    size_penalty = 0.005 * abs(mw - 350)

    # Variacao estocastica controlada
    noise = rng.gauss(0, 0.5)

    binding_affinity = round(
        base_score + hydrophobic_contrib + hbond_contrib +
        flexibility_penalty + aromatic_bonus - size_penalty + noise,
        2
    )
    binding_affinity = max(-12.0, min(-1.0, binding_affinity))

    # Classificacao
    if binding_affinity <= -8:
        classification = "Excelente"
        status = "valid"
    elif binding_affinity <= -6:
        classification = "Bom"
        status = "valid"
    elif binding_affinity <= -4:
        classification = "Moderado"
        status = "warning"
    else:
        classification = "Fraco"
        status = "invalid"

    # Sitios ativos simulados
    active_sites = _identify_active_sites(pdb_data, rng)

    # Interacoes moleculares
    interactions = _predict_interactions(mol, rng)

    return {
        "success": True,
        "binding_affinity": binding_affinity,
        "binding_affinity_unit": "kcal/mol",
        "classification": classification,
        "status": status,
        "active_sites": active_sites,
        "interactions": interactions,
        "ligand_properties": {
            "molecular_weight": round(mw, 2),
            "logp": round(logp, 2),
            "hbd": hbd,
            "hba": hba,
            "tpsa": round(tpsa, 2),
            "rotatable_bonds": rotatable,
        },
        "protein": protein_name,
        "method": "Score estimado por propriedades moleculares (simulacao)",
        "note": "Para resultados de producao, integrar com AutoDock Vina ou UCSF ChimeraX",
    }


def _identify_active_sites(pdb_data: str | None, rng: random.Random) -> list[dict]:
    """Identifica sitios ativos a partir de dados PDB ou gera simulados."""
    if pdb_data:
        sites = []
        residues_near_center = []
        coords = []

        for line in pdb_data.split("\n"):
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    res_name = line[17:20].strip()
                    res_num = int(line[22:26])
                    chain = line[21]
                    coords.append((x, y, z))
                    residues_near_center.append({
                        "residue": res_name,
                        "number": res_num,
                        "chain": chain,
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "z": round(z, 2),
                    })
                except (ValueError, IndexError):
                    continue

        if coords:
            cx = sum(c[0] for c in coords) / len(coords)
            cy = sum(c[1] for c in coords) / len(coords)
            cz = sum(c[2] for c in coords) / len(coords)

            for r in residues_near_center:
                dist = math.sqrt((r["x"] - cx)**2 + (r["y"] - cy)**2 + (r["z"] - cz)**2)
                r["distance_to_center"] = round(dist, 2)

            residues_near_center.sort(key=lambda r: r["distance_to_center"])
            sites = residues_near_center[:10]

            return [{
                "site_id": 1,
                "center": {"x": round(cx, 2), "y": round(cy, 2), "z": round(cz, 2)},
                "residues": sites,
            }]

    # Sitios simulados
    return [{
        "site_id": 1,
        "center": {
            "x": round(rng.uniform(10, 50), 2),
            "y": round(rng.uniform(10, 50), 2),
            "z": round(rng.uniform(10, 50), 2),
        },
        "residues": [
            {"residue": r, "number": rng.randint(50, 300), "chain": "A"}
            for r in rng.sample(["ASP", "GLU", "HIS", "LYS", "ARG", "SER", "THR", "TYR", "CYS", "ASN"], 5)
        ],
    }]


def _predict_interactions(mol, rng: random.Random) -> list[dict]:
    """Prediz tipos de interacoes moleculares."""
    interactions = []

    if Descriptors.NumHDonors(mol) > 0:
        interactions.append({
            "type": "Ligacao de hidrogenio (doador)",
            "count": Descriptors.NumHDonors(mol),
            "strength": "forte",
        })
    if Descriptors.NumHAcceptors(mol) > 0:
        interactions.append({
            "type": "Ligacao de hidrogenio (aceptor)",
            "count": Descriptors.NumHAcceptors(mol),
            "strength": "forte",
        })

    aromatic = rdMolDescriptors.CalcNumAromaticRings(mol)
    if aromatic > 0:
        interactions.append({
            "type": "Pi-stacking",
            "count": aromatic,
            "strength": "moderada",
        })

    if Descriptors.MolLogP(mol) > 2:
        interactions.append({
            "type": "Interacao hidrofobica",
            "count": rng.randint(2, 6),
            "strength": "moderada",
        })

    return interactions
