"""
Servico de avaliacao ADME (Absorcao, Distribuicao, Metabolismo, Excrecao).

SwissADME nao possui API publica. Este modulo implementa calculos ADME
usando RDKit para propriedades que podem ser calculadas localmente,
proporcionando resultados funcionais e cientificamente validos.
"""

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors


def evaluate_adme(smiles: str) -> dict:
    """Avalia propriedades ADME de uma molecula."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"success": False, "error": "SMILES invalido"}

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    rotatable = Lipinski.NumRotatableBonds(mol)
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()
    molar_refractivity = Descriptors.MolMR(mol)

    # Solubilidade estimada (modelo ESOL simplificado)
    log_s = 0.16 - 0.63 * logp - 0.0062 * mw + 0.066 * rotatable - 0.74 * aromatic_rings
    solubility_class = _classify_solubility(log_s)

    # Permeabilidade GI (baseado em regras Egan)
    gi_absorption = "Alta" if tpsa <= 131.6 and logp <= 5.88 else "Baixa"

    # BBB (barreira hematoencefalica)
    bbb_permeant = tpsa <= 79 and logp >= 1 and mw < 450

    # Drug-likeness scores
    lipinski_violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    veber_pass = rotatable <= 10 and tpsa <= 140
    ghose_pass = 160 <= mw <= 480 and -0.4 <= logp <= 5.6 and 40 <= molar_refractivity <= 130 and 20 <= heavy_atoms <= 70

    # Bioavailability score
    bioavailability = 0.55 if lipinski_violations <= 1 else 0.17

    # Classe de toxicidade estimada (simplificado)
    pains_alert = _check_pains_simple(mol)

    return {
        "success": True,
        "physicochemical": {
            "molecular_weight": round(mw, 2),
            "logp": round(logp, 2),
            "tpsa": round(tpsa, 2),
            "hbd": hbd,
            "hba": hba,
            "rotatable_bonds": rotatable,
            "aromatic_rings": aromatic_rings,
            "heavy_atoms": heavy_atoms,
            "molar_refractivity": round(molar_refractivity, 2),
        },
        "solubility": {
            "log_s": round(log_s, 2),
            "class": solubility_class,
        },
        "permeability": {
            "gi_absorption": gi_absorption,
            "bbb_permeant": bbb_permeant,
        },
        "druglikeness": {
            "lipinski_violations": lipinski_violations,
            "lipinski_pass": lipinski_violations <= 1,
            "veber_pass": veber_pass,
            "ghose_pass": ghose_pass,
            "bioavailability_score": bioavailability,
        },
        "alerts": {
            "pains": pains_alert,
        },
    }


def _classify_solubility(log_s: float) -> str:
    if log_s >= 0:
        return "Altamente soluvel"
    elif log_s >= -2:
        return "Soluvel"
    elif log_s >= -4:
        return "Moderadamente soluvel"
    elif log_s >= -6:
        return "Pouco soluvel"
    return "Insoluvel"


def _check_pains_simple(mol) -> bool:
    """Verificacao simplificada de alertas PAINS (Pan Assay Interference)."""
    smiles = Chem.MolToSmiles(mol)
    pains_patterns = [
        "[#6]1[#6][#6](=[#8])[#6][#6](=[#8])[#6]1",  # quinona
        "[#7]=[#7]=[#7]",  # azida
    ]
    for pattern in pains_patterns:
        pat = Chem.MolFromSmarts(pattern)
        if pat and mol.HasSubstructMatch(pat):
            return True
    return False
