"""
Servico de analise de similaridade molecular usando Tanimoto Fingerprints.

Utiliza Morgan Fingerprints (ECFP4) do RDKit para calcular
similaridade entre moleculas via coeficiente de Tanimoto.
"""

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def compute_fingerprint(smiles: str):
    """Calcula Morgan Fingerprint (ECFP4, raio=2, 2048 bits)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)


def tanimoto_similarity(smiles1: str, smiles2: str) -> dict:
    """Calcula similaridade de Tanimoto entre duas moleculas."""
    fp1 = compute_fingerprint(smiles1)
    fp2 = compute_fingerprint(smiles2)

    if fp1 is None:
        return {"success": False, "error": f"SMILES 1 invalido: {smiles1}"}
    if fp2 is None:
        return {"success": False, "error": f"SMILES 2 invalido: {smiles2}"}

    similarity = DataStructs.TanimotoSimilarity(fp1, fp2)

    return {
        "success": True,
        "similarity": round(similarity, 4),
        "smiles1": Chem.MolToSmiles(Chem.MolFromSmiles(smiles1)),
        "smiles2": Chem.MolToSmiles(Chem.MolFromSmiles(smiles2)),
        "classification": _classify(similarity),
    }


def find_similar(query_smiles: str, candidates: list[dict], top_n: int = 10) -> list[dict]:
    """
    Encontra as moleculas mais similares a uma query.
    candidates: lista de dicts com pelo menos {"id": ..., "smiles": ...}
    """
    query_fp = compute_fingerprint(query_smiles)
    if query_fp is None:
        return []

    results = []
    for candidate in candidates:
        fp = compute_fingerprint(candidate["smiles"])
        if fp is None:
            continue

        sim = DataStructs.TanimotoSimilarity(query_fp, fp)
        results.append({
            "id": candidate.get("id"),
            "name": candidate.get("name", ""),
            "smiles": candidate["smiles"],
            "similarity": round(sim, 4),
            "classification": _classify(sim),
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_n]


def similarity_matrix(smiles_list: list[str]) -> dict:
    """Calcula matriz de similaridade NxN entre todas as moleculas."""
    fps = []
    valid_indices = []

    for i, smi in enumerate(smiles_list):
        fp = compute_fingerprint(smi)
        if fp is not None:
            fps.append(fp)
            valid_indices.append(i)

    n = len(fps)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            sim = DataStructs.TanimotoSimilarity(fps[i], fps[j])
            matrix[i][j] = round(sim, 4)
            matrix[j][i] = round(sim, 4)

    return {
        "matrix": matrix,
        "indices": valid_indices,
        "size": n,
    }


def _classify(similarity: float) -> str:
    if similarity >= 0.85:
        return "Muito alta"
    elif similarity >= 0.7:
        return "Alta"
    elif similarity >= 0.5:
        return "Moderada"
    elif similarity >= 0.3:
        return "Baixa"
    return "Muito baixa"
