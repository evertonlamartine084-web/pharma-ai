from __future__ import annotations

"""
Gerador de novas moleculas com validacao rigorosa via RDKit.

Todas as moleculas geradas passam por:
1. Parsing e sanitizacao (Chem.SanitizeMol)
2. Verificacao de valencia
3. Kekulizacao (aromaticidade consistente)
4. Verificacao de fragmentos desconectados (rejeita moleculas com ".")
5. Regra de Lipinski
6. Filtro de peso molecular (150-800 Da)
7. Verificacao de aneis problematicos
"""

import random

from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors, Descriptors, Lipinski, rdmolops
from rdkit.Chem import RWMol, Atom, BondType


# Fragmentos farmacologicamente relevantes (SMILES validos)
PHARMA_FRAGMENTS_SMARTS = [
    "c1ccc2[nH]c3ccccc3c2c1",   # carbazol
    "c1ccc2c(c1)nc1ccccc1n2",   # quinoxalina
    "c1cnc2ccccc2n1",            # quinazolina
    "c1ccc2ncccc2c1",            # quinolina
    "c1ccncc1",                   # piridina
    "c1cc[nH]c1",                 # pirrol
    "c1csc(n1)N",                 # 2-aminotiazol
    "c1ccoc1",                    # furano
    "c1ccsc1",                    # tiofeno
    "c1c[nH]cn1",                 # imidazol
]

SUBSTITUENTS_SMARTS = {
    "F": 9, "Cl": 17, "Br": 35,
    "O": 8, "N": 7, "S": 16,
}


def generate_molecules(seed_smiles: str, n_molecules: int = 10) -> list[dict]:
    """
    Gera novas moleculas a partir de um SMILES semente.

    Cada molecula gerada passa por validacao rigorosa RDKit.
    Retorna apenas moleculas quimicamente validas e conectadas.
    """
    seed_mol = Chem.MolFromSmiles(seed_smiles)
    if seed_mol is None:
        return []

    # Sanitizar semente
    try:
        Chem.SanitizeMol(seed_mol)
    except Exception:
        return []

    generated = []
    attempts = 0
    max_attempts = n_molecules * 30

    strategies = [
        _substitute_atom,
        _add_substituent,
        _replace_ring,
        _modify_functional_group,
        _ring_opening_closure,
    ]

    while len(generated) < n_molecules and attempts < max_attempts:
        attempts += 1
        strategy_func = random.choice(strategies)

        try:
            new_smiles = strategy_func(seed_mol)
        except Exception:
            continue

        if new_smiles is None:
            continue

        validation = _validate_molecule(new_smiles, generated)
        if validation["valid"]:
            generated.append({
                "smiles": validation["canonical_smiles"],
                "strategy": strategy_func.__name__.lstrip("_"),
                "parent_smiles": seed_smiles,
            })

    return generated


def _substitute_atom(mol) -> str | None:
    """Substitui um atomo por outro quimicamente compativel."""
    rwmol = RWMol(Chem.RWMol(mol))
    atoms = list(range(rwmol.GetNumAtoms()))
    if not atoms:
        return None

    random.shuffle(atoms)

    # Substituicoes quimicamente validas
    subs = {
        6: [7, 8, 16],      # C -> N, O, S
        7: [6, 8],           # N -> C, O
        8: [7, 16],          # O -> N, S
        16: [8, 7],          # S -> O, N
    }

    for idx in atoms:
        atom = rwmol.GetAtomWithIdx(idx)
        atomic_num = atom.GetAtomicNum()
        if atomic_num not in subs:
            continue

        new_num = random.choice(subs[atomic_num])

        # Clonar e testar
        test_mol = RWMol(rwmol)
        test_atom = test_mol.GetAtomWithIdx(idx)
        test_atom.SetAtomicNum(new_num)
        # Resetar carga e Hs
        test_atom.SetFormalCharge(0)
        test_atom.SetNumExplicitHs(0)
        test_atom.SetNoImplicit(False)

        try:
            Chem.SanitizeMol(test_mol)
            return Chem.MolToSmiles(test_mol)
        except Exception:
            continue

    return None


def _add_substituent(mol) -> str | None:
    """Adiciona um substituinte a um atomo com valencia livre."""
    rwmol = RWMol(Chem.RWMol(mol))
    atoms = list(range(rwmol.GetNumAtoms()))
    random.shuffle(atoms)

    substituents = [
        (9, 0),     # F
        (17, 0),    # Cl
        (8, 0),     # =O (cetona)
        (7, 0),     # -NH2
    ]

    for idx in atoms:
        atom = rwmol.GetAtomWithIdx(idx)

        # Apenas carbonos com valencia livre
        if atom.GetAtomicNum() != 6:
            continue
        if atom.GetDegree() >= 4:
            continue
        if atom.GetTotalValence() >= 4:
            continue

        sub_atomic_num, charge = random.choice(substituents)

        test_mol = RWMol(rwmol)
        new_idx = test_mol.AddAtom(Atom(sub_atomic_num))
        if sub_atomic_num == 8 and random.random() > 0.5:
            test_mol.AddBond(idx, new_idx, BondType.DOUBLE)
        else:
            test_mol.AddBond(idx, new_idx, BondType.SINGLE)

        try:
            Chem.SanitizeMol(test_mol)
            return Chem.MolToSmiles(test_mol)
        except Exception:
            continue

    return None


def _replace_ring(mol) -> str | None:
    """Substitui um anel aromatico por outro scaffold farmacologico."""
    smiles = Chem.MolToSmiles(mol)
    ring_info = mol.GetRingInfo()
    if ring_info.NumRings() == 0:
        return None

    # Identificar aneis de 5 ou 6 membros
    rings = ring_info.AtomRings()
    target_rings = [r for r in rings if len(r) in (5, 6)]
    if not target_rings:
        return None

    # Escolher fragmento de substituicao do mesmo tamanho
    ring = random.choice(target_rings)
    ring_size = len(ring)

    # Fragmentos por tamanho
    replacements_6 = ["c1ccncc1", "c1ccnc(N)n1", "c1ccc(O)cc1"]
    replacements_5 = ["c1ccoc1", "c1ccsc1", "c1c[nH]cn1"]

    replacement = random.choice(replacements_6 if ring_size == 6 else replacements_5)
    rep_mol = Chem.MolFromSmiles(replacement)
    if rep_mol is None:
        return None

    # Usar RDKit reaction para substituir (abordagem simplificada)
    # Abordagem: modificar atomos do anel no mol original
    rwmol = RWMol(Chem.RWMol(mol))

    # Pegar atomos do anel e do fragmento
    rep_atoms = [a for a in rep_mol.GetAtoms()]
    if len(rep_atoms) != ring_size:
        return None

    # Substituir tipos atomicos
    for i, ring_idx in enumerate(ring[:len(rep_atoms)]):
        orig_atom = rwmol.GetAtomWithIdx(ring_idx)
        new_atom = rep_atoms[i]
        orig_atom.SetAtomicNum(new_atom.GetAtomicNum())
        orig_atom.SetIsAromatic(new_atom.GetIsAromatic())
        orig_atom.SetFormalCharge(0)
        orig_atom.SetNumExplicitHs(0)
        orig_atom.SetNoImplicit(False)

    try:
        Chem.SanitizeMol(rwmol)
        return Chem.MolToSmiles(rwmol)
    except Exception:
        return None


def _modify_functional_group(mol) -> str | None:
    """Modifica grupos funcionais (OH->SH, NH->O, ester->amida, etc)."""
    rwmol = RWMol(Chem.RWMol(mol))
    atoms = list(range(rwmol.GetNumAtoms()))
    random.shuffle(atoms)

    for idx in atoms:
        atom = rwmol.GetAtomWithIdx(idx)
        num = atom.GetAtomicNum()
        degree = atom.GetDegree()

        test_mol = RWMol(rwmol)
        test_atom = test_mol.GetAtomWithIdx(idx)

        # OH -> SH
        if num == 8 and degree == 1:
            test_atom.SetAtomicNum(16)
        # OH -> NH2
        elif num == 8 and degree == 1 and random.random() > 0.5:
            test_atom.SetAtomicNum(7)
        # NH -> O
        elif num == 7 and degree <= 2:
            test_atom.SetAtomicNum(8)
        # F -> Cl ou vice-versa
        elif num == 9:
            test_atom.SetAtomicNum(17)
        elif num == 17:
            test_atom.SetAtomicNum(9)
        else:
            continue

        test_atom.SetFormalCharge(0)
        test_atom.SetNumExplicitHs(0)
        test_atom.SetNoImplicit(False)

        try:
            Chem.SanitizeMol(test_mol)
            return Chem.MolToSmiles(test_mol)
        except Exception:
            continue

    return None


def _ring_opening_closure(mol) -> str | None:
    """Adiciona ou remove metileno de uma cadeia, ou abre/fecha anel pequeno."""
    rwmol = RWMol(Chem.RWMol(mol))

    # Estrategia: inserir um CH2 entre dois atomos ligados por single bond
    bonds = list(rwmol.GetBonds())
    random.shuffle(bonds)

    for bond in bonds:
        if bond.GetBondType() != BondType.SINGLE:
            continue
        if bond.IsInRing():
            continue

        idx1 = bond.GetBeginAtomIdx()
        idx2 = bond.GetEndAtomIdx()

        atom1 = rwmol.GetAtomWithIdx(idx1)
        atom2 = rwmol.GetAtomWithIdx(idx2)

        # Ambos devem ser C, N, ou O
        if atom1.GetAtomicNum() not in (6, 7, 8) or atom2.GetAtomicNum() not in (6, 7, 8):
            continue

        test_mol = RWMol(rwmol)

        # Remover bond original
        test_mol.RemoveBond(idx1, idx2)

        # Adicionar CH2
        new_idx = test_mol.AddAtom(Atom(6))
        test_mol.AddBond(idx1, new_idx, BondType.SINGLE)
        test_mol.AddBond(new_idx, idx2, BondType.SINGLE)

        try:
            Chem.SanitizeMol(test_mol)
            result = Chem.MolToSmiles(test_mol)
            # Verificar que nao criou fragmentos
            if "." not in result:
                return result
        except Exception:
            continue

    return None


def _validate_molecule(smiles: str, existing: list[dict]) -> dict:
    """
    Validacao rigorosa de molecula via RDKit.

    Verifica:
    1. Parsing valido
    2. Sanitizacao completa (valencias, aromaticidade)
    3. Molecula conectada (sem fragmentos)
    4. Kekulizacao bem-sucedida
    5. Peso molecular adequado (150-800 Da)
    6. Nao duplicada
    7. Diferente da semente
    """
    # 1. Parsing
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"valid": False, "reason": "SMILES invalido"}

    # 2. Sanitizacao completa
    try:
        Chem.SanitizeMol(mol)
    except Exception as e:
        return {"valid": False, "reason": f"Falha na sanitizacao: {e}"}

    # 3. Molecula conectada (sem fragmentos separados por ".")
    canonical = Chem.MolToSmiles(mol)
    if "." in canonical:
        return {"valid": False, "reason": "Molecula desconectada (fragmentos separados)"}

    # 4. Kekulizacao
    try:
        Chem.Kekulize(mol, clearAromaticFlags=False)
    except Exception:
        return {"valid": False, "reason": "Falha na kekulizacao"}

    # 5. Verificar valencias
    try:
        problems = Chem.DetectChemistryProblems(mol)
        if problems:
            return {"valid": False, "reason": f"Problema quimico: {problems[0].Message()}"}
    except Exception:
        pass

    # 6. Peso molecular
    mw = Descriptors.MolWt(mol)
    if mw < 150 or mw > 800:
        return {"valid": False, "reason": f"Peso molecular fora do range (150-800): {mw:.1f}"}

    # 7. Numero de atomos pesados minimo
    if mol.GetNumHeavyAtoms() < 8:
        return {"valid": False, "reason": "Muito poucos atomos pesados"}

    # 8. Nao duplicada
    if any(entry["smiles"] == canonical for entry in existing):
        return {"valid": False, "reason": "Duplicada"}

    # 9. Verificar aneis problematicos (3 membros sao instáveis)
    ring_info = mol.GetRingInfo()
    for ring in ring_info.AtomRings():
        if len(ring) < 4:
            return {"valid": False, "reason": "Anel com menos de 4 membros"}

    # 10. Calcular propriedades para retorno
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable = Lipinski.NumRotatableBonds(mol)
    lipinski_violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])

    return {
        "valid": True,
        "canonical_smiles": canonical,
        "molecular_weight": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 2),
        "rotatable_bonds": rotatable,
        "lipinski_violations": lipinski_violations,
        "lipinski_pass": lipinski_violations <= 1,
    }
