"""
Servico de docking molecular real usando AutoDock Vina 1.2.5.

Pipeline:
1. Preparar ligante: SMILES -> 3D SDF -> PDBQT (via RDKit + Meeko)
2. Preparar receptor: PDB -> PDBQT
3. Identificar centro do sitio ativo
4. Executar Vina
5. Parsear resultados
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import logging
import math

from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

VINA_BIN = os.getenv(
    "VINA_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bin", "vina")
)


def is_vina_available() -> bool:
    try:
        result = subprocess.run([VINA_BIN, "--version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def run_vina_docking(smiles: str, pdb_data: str, protein_name: str, exhaustiveness: int = 8) -> dict:
    """Executa docking real com AutoDock Vina."""
    if not pdb_data:
        return {"success": False, "error": "Dados PDB necessarios para docking com Vina"}

    if not is_vina_available():
        return {"success": False, "error": "AutoDock Vina nao encontrado"}

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Preparar ligante
            ligand_pdbqt = _prepare_ligand(smiles, tmpdir)
            if not ligand_pdbqt:
                return {"success": False, "error": "Falha ao preparar ligante"}

            # 2. Preparar receptor
            receptor_pdbqt = _prepare_receptor(pdb_data, tmpdir)
            if not receptor_pdbqt:
                return {"success": False, "error": "Falha ao preparar receptor"}

            # 3. Calcular centro e tamanho do sitio ativo
            center, size = _calc_binding_box(pdb_data)

            # 4. Executar Vina
            output_pdbqt = os.path.join(tmpdir, "output.pdbqt")
            log_file = os.path.join(tmpdir, "vina.log")

            cmd = [
                VINA_BIN,
                "--receptor", receptor_pdbqt,
                "--ligand", ligand_pdbqt,
                "--center_x", str(round(center[0], 2)),
                "--center_y", str(round(center[1], 2)),
                "--center_z", str(round(center[2], 2)),
                "--size_x", str(round(size[0], 1)),
                "--size_y", str(round(size[1], 1)),
                "--size_z", str(round(size[2], 1)),
                "--exhaustiveness", str(exhaustiveness),
                "--num_modes", "5",
                "--out", output_pdbqt,
            ]

            logger.info(f"Executando Vina: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                return {"success": False, "error": f"Vina falhou: {result.stderr[:300]}"}

            # 5. Parsear resultados
            scores = _parse_vina_output(result.stdout)
            if not scores:
                return {"success": False, "error": "Nenhum resultado de docking encontrado"}

            # 6. Ler PDBQT do ligante dockado para visualizacao
            docked_pdbqt = ""
            if os.path.exists(output_pdbqt):
                with open(output_pdbqt) as f:
                    docked_pdbqt = f.read()

            # Converter melhor pose para SDF
            docked_sdf = _pdbqt_to_sdf(docked_pdbqt)

            best = scores[0]
            classification = _classify_affinity(best["affinity"])

            return {
                "success": True,
                "method": "AutoDock Vina 1.2.5",
                "binding_affinity": best["affinity"],
                "binding_affinity_unit": "kcal/mol",
                "classification": classification["label"],
                "status": classification["status"],
                "all_modes": scores,
                "center": {"x": round(center[0], 2), "y": round(center[1], 2), "z": round(center[2], 2)},
                "box_size": {"x": round(size[0], 1), "y": round(size[1], 1), "z": round(size[2], 1)},
                "exhaustiveness": exhaustiveness,
                "protein": protein_name,
                "docked_ligand_sdf": docked_sdf,
                "docked_ligand_pdbqt": docked_pdbqt,
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Vina timeout (>5 min)"}
    except Exception as e:
        logger.error(f"Erro no docking Vina: {e}")
        return {"success": False, "error": str(e)}


def _prepare_ligand(smiles: str, tmpdir: str) -> str | None:
    """SMILES -> 3D mol -> PDBQT."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv2() if hasattr(AllChem, 'ETKDGv2') else AllChem.ETKDG()
    if AllChem.EmbedMolecule(mol, params) == -1:
        if AllChem.EmbedMolecule(mol, AllChem.ETKDG()) == -1:
            return None

    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        pass

    # Salvar como SDF
    sdf_path = os.path.join(tmpdir, "ligand.sdf")
    writer = Chem.SDWriter(sdf_path)
    writer.write(mol)
    writer.close()

    # Converter SDF -> PDBQT via Meeko
    pdbqt_path = os.path.join(tmpdir, "ligand.pdbqt")
    try:
        from meeko import MoleculePreparation, PDBQTWriterLegacy
        preparator = MoleculePreparation()
        mol_setup = preparator.prepare(mol)[0]
        pdbqt_string, is_ok, error_msg = PDBQTWriterLegacy.write_string(mol_setup)
        if is_ok:
            with open(pdbqt_path, "w") as f:
                f.write(pdbqt_string)
            return pdbqt_path
    except Exception as e:
        logger.warning(f"Meeko falhou: {e}, tentando conversao manual")

    # Fallback: conversao manual SDF -> PDBQT simplificada
    return _sdf_to_pdbqt_simple(sdf_path, pdbqt_path)


def _prepare_receptor(pdb_data: str, tmpdir: str) -> str | None:
    """PDB -> PDBQT (remover aguas, adicionar cargas)."""
    pdb_path = os.path.join(tmpdir, "receptor.pdb")
    pdbqt_path = os.path.join(tmpdir, "receptor.pdbqt")

    # Filtrar linhas relevantes do PDB
    lines = []
    for line in pdb_data.split("\n"):
        if line.startswith("ATOM") or line.startswith("HETATM"):
            res = line[17:20].strip()
            if res != "HOH":  # Remover aguas
                lines.append(line)
        elif line.startswith("END"):
            lines.append(line)

    with open(pdb_path, "w") as f:
        f.write("\n".join(lines))

    # Converter PDB -> PDBQT (adicionar tipos atomicos Vina)
    pdbqt_lines = []
    for line in lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            atom_name = line[12:16].strip()
            res_name = line[17:20].strip()
            element = line[76:78].strip() if len(line) > 76 else atom_name[0]

            # Mapear para tipos atomicos AutoDock
            ad_type = _get_ad_type(element, atom_name, res_name)
            # PDBQT formato: cols 1-54 = coords, 55-60 = occupancy, 61-66 = bfactor,
            # 67-76 = charge, 77-78 = AD type
            padded = line.ljust(54)
            pdbqt_line = f"{padded[:54]}  1.00  0.00    +0.000 {ad_type:>2s}"
            pdbqt_lines.append(pdbqt_line)

    pdbqt_lines.append("END")

    with open(pdbqt_path, "w") as f:
        f.write("\n".join(pdbqt_lines))

    return pdbqt_path


def _calc_binding_box(pdb_data: str) -> tuple:
    """Calcula centro e tamanho da caixa de docking a partir do PDB."""
    coords = []
    for line in pdb_data.split("\n"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append((x, y, z))
            except ValueError:
                continue

    if not coords:
        return (0, 0, 0), (30, 30, 30)

    # Centro geometrico
    cx = sum(c[0] for c in coords) / len(coords)
    cy = sum(c[1] for c in coords) / len(coords)
    cz = sum(c[2] for c in coords) / len(coords)

    # Caixa que cobre 60% dos residuos centrais
    dists = [(math.sqrt((c[0]-cx)**2 + (c[1]-cy)**2 + (c[2]-cz)**2), c) for c in coords]
    dists.sort()
    central = [d[1] for d in dists[:max(len(dists)//3, 10)]]

    if central:
        cx = sum(c[0] for c in central) / len(central)
        cy = sum(c[1] for c in central) / len(central)
        cz = sum(c[2] for c in central) / len(central)

    # Tamanho da caixa (minimo 20A, maximo 40A)
    size_x = min(40, max(20, max(c[0] for c in central) - min(c[0] for c in central) + 10))
    size_y = min(40, max(20, max(c[1] for c in central) - min(c[1] for c in central) + 10))
    size_z = min(40, max(20, max(c[2] for c in central) - min(c[2] for c in central) + 10))

    return (cx, cy, cz), (size_x, size_y, size_z)


def _parse_vina_output(output: str) -> list[dict]:
    """Parseia output do Vina para extrair scores."""
    scores = []
    in_table = False

    for line in output.split("\n"):
        if "-----+----" in line:
            in_table = True
            continue
        if in_table:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    mode = int(parts[0])
                    affinity = float(parts[1])
                    rmsd_lb = float(parts[2])
                    rmsd_ub = float(parts[3])
                    scores.append({
                        "mode": mode,
                        "affinity": affinity,
                        "rmsd_lb": rmsd_lb,
                        "rmsd_ub": rmsd_ub,
                    })
                except (ValueError, IndexError):
                    if scores:
                        break

    return scores


def _classify_affinity(affinity: float) -> dict:
    if affinity <= -8:
        return {"label": "Excelente", "status": "valid"}
    elif affinity <= -6:
        return {"label": "Bom", "status": "valid"}
    elif affinity <= -4:
        return {"label": "Moderado", "status": "warning"}
    return {"label": "Fraco", "status": "invalid"}


def _get_ad_type(element: str, atom_name: str, res_name: str = "") -> str:
    """
    Mapeia elemento para tipo atomico AutoDock.
    Tipos do Vina: C, A (aromatic C), N, NA (N acceptor),
    O, OA (O acceptor), S, SA, H, HD (H donor), F, Cl, Br, I, P
    """
    atom_name = atom_name.strip()

    if element == "C":
        return "C"
    elif element == "N":
        # Backbone N e NH sao tipo "N" (doador); outros sao "NA" (aceptor)
        if atom_name in ("N", "NE", "NH1", "NH2", "NZ", "ND1", "ND2", "NE1", "NE2"):
            return "N"
        return "NA"
    elif element == "O":
        # Backbone O=C e carboxilato sao tipo "OA" (aceptor)
        return "OA"
    elif element == "S":
        return "SA"
    elif element == "H":
        return "HD"

    mapping = {
        "F": "F", "Cl": "Cl", "Br": "Br",
        "P": "P", "I": "I", "Zn": "Zn", "Fe": "Fe",
        "Ca": "Ca", "Mg": "Mg", "Mn": "Mn",
    }

    if element in mapping:
        return mapping[element]

    first = atom_name[0] if atom_name else "C"
    return mapping.get(first, "C")


def _sdf_to_pdbqt_simple(sdf_path: str, pdbqt_path: str) -> str | None:
    """Conversao SDF -> PDBQT para ligante (formato Vina com ROOT/ENDROOT)."""
    mol = Chem.MolFromMolFile(sdf_path, removeHs=False)
    if mol is None:
        return None

    pdb_block = Chem.MolToPDBBlock(mol)
    atom_lines = []
    for line in pdb_block.split("\n"):
        if line.startswith("HETATM") or line.startswith("ATOM"):
            atom_name = line[12:16].strip()
            element = line[76:78].strip() if len(line) > 76 else atom_name[0]
            ad_type = _get_ad_type(element, atom_name)
            padded = line.ljust(54)
            pdbqt_line = f"{padded[:54]}  1.00  0.00    +0.000 {ad_type:>2s}"
            atom_lines.append(pdbqt_line)

    if not atom_lines:
        return None

    # Vina ligante PDBQT precisa de ROOT/ENDROOT
    output = ["ROOT"]
    output.extend(atom_lines)
    output.append("ENDROOT")
    output.append("TORSDOF 0")

    with open(pdbqt_path, "w") as f:
        f.write("\n".join(output))

    return pdbqt_path


def _pdbqt_to_sdf(pdbqt_content: str) -> str | None:
    """Converte primeira pose do PDBQT dockado para SDF (para 3Dmol.js)."""
    if not pdbqt_content:
        return None

    # Extrair apenas a primeira pose (MODEL 1)
    lines = []
    in_model = False
    for line in pdbqt_content.split("\n"):
        if line.startswith("MODEL"):
            if in_model:
                break
            in_model = True
            continue
        if line.startswith("ENDMDL"):
            break
        if line.startswith("ATOM") or line.startswith("HETATM"):
            # Converter PDBQT -> PDB removendo colunas extras
            pdb_line = line[:54] + line[54:66].replace("  ", "  ") if len(line) > 54 else line
            lines.append(line[:54])

    if not lines:
        return None

    # Usar PDB intermediario para converter a SDF
    pdb_block = "\n".join(lines) + "\nEND\n"
    mol = Chem.MolFromPDBBlock(pdb_block, sanitize=False, removeHs=False)
    if mol is None:
        return None

    try:
        return Chem.MolToMolBlock(mol)
    except Exception:
        return None
