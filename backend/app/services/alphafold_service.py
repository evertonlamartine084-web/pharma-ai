import requests

ALPHAFOLD_API_BASE = "https://alphafold.ebi.ac.uk/api"


def fetch_structure_by_uniprot(uniprot_id: str) -> dict:
    """Busca estrutura predita pelo AlphaFold via UniProt ID."""
    url = f"{ALPHAFOLD_API_BASE}/prediction/{uniprot_id}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            entry = data[0] if isinstance(data, list) else data
            pdb_url = entry.get("pdbUrl")
            if pdb_url:
                pdb_resp = requests.get(pdb_url, timeout=60)
                if pdb_resp.status_code == 200:
                    return {
                        "success": True,
                        "uniprot_id": uniprot_id,
                        "pdb_data": pdb_resp.text,
                        "confidence": entry.get("globalMetricValue"),
                        "organism": entry.get("organismScientificName", ""),
                        "gene": entry.get("gene", ""),
                    }
            return {"success": False, "error": "PDB nao encontrado na resposta"}
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def parse_pdb_content(pdb_text: str) -> dict:
    """Extrai informacoes basicas de um arquivo PDB."""
    lines = pdb_text.strip().split("\n")
    title = ""
    atoms = 0
    residues = set()

    for line in lines:
        if line.startswith("TITLE"):
            title += line[10:].strip() + " "
        elif line.startswith("ATOM"):
            atoms += 1
            res_name = line[17:20].strip()
            res_seq = line[22:26].strip()
            chain = line[21]
            residues.add(f"{chain}:{res_name}{res_seq}")

    return {
        "title": title.strip(),
        "atom_count": atoms,
        "residue_count": len(residues),
    }


# Proteinas mock de Leishmania para banco inicial
LEISHMANIA_PROTEINS = [
    {
        "name": "Pteridine reductase 1 (PTR1)",
        "organism": "Leishmania major",
        "uniprot_id": "Q01782",
        "sequence": (
            "MAQYDKLVIGAGARGISAAIDAARGLQPVAVLEARTGLSVDLYVDSATLTGRRL"
            "PEEAKRAFEEITAKEYGKSYALDNVTPILETELGAPLLIDTAVYALKETGRLHE"
            "TYDLNPKDHEHTIPYADYGNINEAITDEELKKLVEALTAKFGAEHRTINASVYV"
            "AHTKEAHFTGTHTGELGHIPRYSVEDLKTRLKAYEENGIALDLVNEHIAHIRPK"
            "VITSDDLHEEFDLAIDYNHPGQLLQEGLHVIGSVEELVDNALKNREAGKIL"
        ),
    },
    {
        "name": "Trypanothione reductase (TryR)",
        "organism": "Leishmania infantum",
        "uniprot_id": "A4I898",
        "sequence": (
            "MSDFSAVVIGSGPAASYYAARSLQSAEVVALIEARGS"
            "VTLNYHKNTSAKGNCILKKSVCIGGGNTAVEEALYL"
        ),
    },
]
