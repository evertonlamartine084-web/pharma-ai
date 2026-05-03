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
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors


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

        # Aceitar ATOM (proteina) e HETATM (molecula pequena)
        for line in pdb_data.split("\n"):
            is_protein_ca = line.startswith("ATOM") and line[12:16].strip() == "CA"
            is_hetatm = line.startswith("HETATM")
            if not (is_protein_ca or is_hetatm):
                continue
            if True:
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


def calc_3d_interactions(pdb_data: str, ligand_sdf: str) -> list[dict]:
    """Calcula interacoes 3D entre alvo (PDB) e ligante (SDF) com distancias."""
    if not pdb_data or not ligand_sdf:
        return []

    # Extrair coordenadas do alvo (PDB)
    target_atoms = []
    for line in pdb_data.split("\n"):
        if line.startswith("ATOM") or line.startswith("HETATM"):
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                element = line[76:78].strip() if len(line) > 76 else line[12:16].strip()[0]
                atom_name = line[12:16].strip()
                target_atoms.append({"x": x, "y": y, "z": z, "element": element, "name": atom_name})
            except (ValueError, IndexError):
                continue

    # Extrair coordenadas do ligante (SDF/MOL)
    ligand_atoms = []
    mol = Chem.MolFromMolBlock(ligand_sdf, sanitize=False)
    if mol and mol.GetNumConformers() > 0:
        conf = mol.GetConformer()
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            atom = mol.GetAtomWithIdx(i)
            ligand_atoms.append({
                "x": pos.x, "y": pos.y, "z": pos.z,
                "element": atom.GetSymbol(),
                "idx": i,
            })

    if not target_atoms or not ligand_atoms:
        return []

    # Calcular contatos proximos (< 4A)
    contacts = []
    hbond_donors = {"N", "O"}
    hbond_acceptors = {"N", "O", "F"}

    for ta in target_atoms:
        for la in ligand_atoms:
            dx = ta["x"] - la["x"]
            dy = ta["y"] - la["y"]
            dz = ta["z"] - la["z"]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)

            if dist > 4.0 or dist < 0.5:
                continue

            # Classificar tipo de interacao
            itype = "Van der Waals"
            if dist <= 3.5 and (ta["element"] in hbond_donors and la["element"] in hbond_acceptors):
                itype = "Ligacao de hidrogenio"
            elif dist <= 3.5 and (ta["element"] in hbond_acceptors and la["element"] in hbond_donors):
                itype = "Ligacao de hidrogenio"
            elif dist <= 4.0 and ta["element"] == "C" and la["element"] == "C":
                itype = "Interacao hidrofobica"

            contacts.append({
                "type": itype,
                "distance": round(dist, 2),
                "target_atom": ta["name"],
                "ligand_atom_idx": la["idx"],
                "target_pos": {"x": round(ta["x"], 2), "y": round(ta["y"], 2), "z": round(ta["z"], 2)},
                "ligand_pos": {"x": round(la["x"], 2), "y": round(la["y"], 2), "z": round(la["z"], 2)},
            })

    # Ordenar por distancia e pegar os mais relevantes
    contacts.sort(key=lambda c: c["distance"])

    # Filtrar: maximo 1 por par tipo+distancia similar
    filtered = []
    seen = set()
    for c in contacts:
        key = f"{c['type']}_{c['target_atom']}_{c['ligand_atom_idx']}"
        if key not in seen:
            seen.add(key)
            filtered.append(c)
        if len(filtered) >= 15:
            break

    return filtered


def generate_ligand_sdf(smiles: str, center_x: float, center_y: float, center_z: float) -> str | None:
    """Gera SDF 3D do ligante posicionado no centro do sitio ativo."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv2() if hasattr(AllChem, 'ETKDGv2') else AllChem.ETKDG()
    result = AllChem.EmbedMolecule(mol, params)
    if result == -1:
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    if result == -1:
        return None

    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        pass

    # Mover ligante para o centro do sitio ativo
    conf = mol.GetConformer()
    positions = conf.GetPositions()
    centroid = positions.mean(axis=0)
    translation = [center_x - centroid[0], center_y - centroid[1], center_z - centroid[2]]

    for i in range(mol.GetNumAtoms()):
        pos = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, (
            pos.x + translation[0],
            pos.y + translation[1],
            pos.z + translation[2],
        ))

    mol = Chem.RemoveHs(mol)
    return Chem.MolToMolBlock(mol)
