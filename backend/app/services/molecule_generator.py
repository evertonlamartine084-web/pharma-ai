from __future__ import annotations

import random

from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

# Fragmentos farmacologicamente relevantes para Leishmaniose
PHARMA_FRAGMENTS = [
    "c1ccc2[nH]c3ccccc3c2c1",   # carbazol
    "c1ccc2c(c1)nc1ccccc1n2",   # quinoxalina
    "c1cnc2ccccc2n1",            # quinazolina
    "c1ccc2ncccc2c1",            # quinolina
    "c1ccc(cc1)N",               # anilina
    "C1CCNCC1",                   # piperidina
    "C1CCNC1",                    # pirrolidina
    "c1cc[nH]c1",                 # pirrol
    "c1ccncc1",                   # piridina
    "c1csc(n1)N",                 # 2-aminotiazol
    "c1ccc(cc1)O",               # fenol
    "c1ccc(cc1)F",               # fluorobenzeno
    "C(=O)N",                     # amida
    "S(=O)(=O)N",                 # sulfonamida
]

LINKERS = ["C", "CC", "CCC", "C=C", "CC(=O)", "CCO", "CCN", "C(=O)N"]
SUBSTITUENTS = ["F", "Cl", "Br", "O", "N", "C(=O)O", "C#N", "C(F)(F)F", "OC"]


def generate_molecules(seed_smiles: str, n_molecules: int = 10) -> list[dict]:
    """
    Gera novas moleculas a partir de um SMILES semente.

    Estrategias:
    1. Mutacao de substituintes
    2. Fusao de fragmentos
    3. Variacao de scaffold
    """
    seed_mol = Chem.MolFromSmiles(seed_smiles)
    if seed_mol is None:
        return []

    generated = []
    attempts = 0
    max_attempts = n_molecules * 20

    while len(generated) < n_molecules and attempts < max_attempts:
        attempts += 1
        strategy = random.choice(["mutate", "fragment_merge", "scaffold_hop"])

        new_smiles = None
        if strategy == "mutate":
            new_smiles = _mutate_molecule(seed_smiles)
        elif strategy == "fragment_merge":
            new_smiles = _fragment_merge(seed_smiles)
        else:
            new_smiles = _scaffold_hop()

        if new_smiles and _is_valid_and_unique(new_smiles, generated):
            mol = Chem.MolFromSmiles(new_smiles)
            canonical = Chem.MolToSmiles(mol)
            generated.append({
                "smiles": canonical,
                "strategy": strategy,
                "parent_smiles": seed_smiles,
            })

    return generated


def _mutate_molecule(smiles: str) -> str | None:
    """Substitui um atomo ou grupo funcional."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    try:
        rwmol = Chem.RWMol(mol)
        atoms = list(range(rwmol.GetNumAtoms()))
        if not atoms:
            return None

        idx = random.choice(atoms)
        atom = rwmol.GetAtomWithIdx(idx)

        if atom.GetSymbol() == "C" and atom.GetDegree() < 4:
            sub = random.choice(SUBSTITUENTS)
            new_smiles = smiles + "." + sub
            combo = Chem.MolFromSmiles(new_smiles)
            if combo:
                return Chem.MolToSmiles(combo)

        replacements = {"C": "N", "N": "O", "O": "S", "S": "N"}
        old_sym = atom.GetSymbol()
        if old_sym in replacements:
            atom.SetAtomicNum(Chem.GetPeriodicTable().GetAtomicNumber(replacements[old_sym]))
            result = Chem.MolToSmiles(rwmol)
            check = Chem.MolFromSmiles(result)
            if check:
                return result
    except Exception:
        pass
    return None


def _fragment_merge(smiles: str) -> str | None:
    """Combina o scaffold da semente com fragmentos farmacologicos."""
    try:
        fragment = random.choice(PHARMA_FRAGMENTS)
        linker = random.choice(LINKERS)
        combined = f"{smiles}.{linker}.{fragment}"
        mol = Chem.MolFromSmiles(combined)
        if mol:
            return Chem.MolToSmiles(mol)
    except Exception:
        pass
    return None


def _scaffold_hop() -> str | None:
    """Gera molecula a partir de combinacao de fragmentos."""
    try:
        f1 = random.choice(PHARMA_FRAGMENTS)
        f2 = random.choice(PHARMA_FRAGMENTS)
        linker = random.choice(LINKERS)

        combined = f"{f1}.{linker}.{f2}"
        mol = Chem.MolFromSmiles(combined)
        if mol:
            return Chem.MolToSmiles(mol)
    except Exception:
        pass
    return None


def _is_valid_and_unique(smiles: str, existing: list[dict]) -> bool:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False

    mw = rdMolDescriptors.CalcExactMolWt(mol)
    if mw < 100 or mw > 800:
        return False

    canonical = Chem.MolToSmiles(mol)
    return all(entry["smiles"] != canonical for entry in existing)
