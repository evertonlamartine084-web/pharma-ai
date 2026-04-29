"""
Scraper para SwissADME usando Playwright.

Submete SMILES (individual ou batch) ao SwissADME e extrai resultados
da variavel textForClipBoard que contem todos os dados em formato CSV.

Requer: pip install playwright && python -m playwright install chromium
"""

import re
import csv
import io
import logging

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


def fetch_swissadme(smiles: str, timeout_ms: int = 60000) -> dict:
    """Consulta SwissADME para uma unica molecula."""
    results = fetch_swissadme_batch([smiles], timeout_ms)
    if results and results[0].get("success"):
        return results[0]
    return {"success": False, "error": results[0].get("error", "Erro desconhecido") if results else "Sem resultado"}


def fetch_swissadme_batch(smiles_list: list, timeout_ms: int = 120000) -> list:
    """
    Consulta SwissADME para multiplas moleculas de uma vez.
    Retorna lista de dicts, um por molecula.
    """
    if not HAS_PLAYWRIGHT:
        return [{"success": False, "error": "Playwright nao instalado"}] * len(smiles_list)

    if not smiles_list:
        return []

    try:
        return _scrape_swissadme_batch(smiles_list, timeout_ms)
    except Exception as e:
        logger.error(f"Erro ao consultar SwissADME batch: {e}")
        return [{"success": False, "error": str(e)}] * len(smiles_list)


def _scrape_swissadme_batch(smiles_list: list, timeout_ms: int) -> list:
    # SwissADME aceita multiplos SMILES separados por newline
    smiles_text = "\\n".join(s.replace("\\", "\\\\").replace("'", "\\'") for s in smiles_list)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://www.swissadme.ch/index.php", timeout=30000)

        page.evaluate(f"""
            var area = document.getElementById('smiles');
            area.value = '{smiles_text}';
            var inputs = document.querySelectorAll('input[name="smiles"]');
            for (var i = 0; i < inputs.length; i++) {{
                if (inputs[i].form && inputs[i].form.id === 'myForm') {{
                    inputs[i].value = '{smiles_text}';
                }}
            }}
            document.getElementById('myForm').submit();
        """)

        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_selector("text=Molecular weight", timeout=timeout_ms)
        content = page.content()
        browser.close()

    return _parse_clipboard_csv_batch(content, len(smiles_list))


def _parse_clipboard_csv_batch(html: str, expected_count: int) -> list:
    """Extrai dados de todas as moleculas do CSV clipboard."""
    all_data = re.findall(
        r'textForClipBoard\s*=\s*textForClipBoard\s*\+\s*"(.*?)\\n";',
        html
    )

    if len(all_data) < 2:
        return [{"success": False, "error": "Dados CSV nao encontrados"}] * expected_count

    header_line = all_data[0]
    headers = [h.strip() for h in header_line.split(",")]

    results = []
    for data_line in all_data[1:]:
        # Limpar formato "+" do SwissADME
        cleaned = data_line.replace(',"+"', ',').replace('"+"', '')
        cleaned = re.sub(r',\s+', ',', cleaned)

        # Parse CSV
        try:
            reader = csv.DictReader(io.StringIO(header_line + "\n" + cleaned))
            row = next(reader, None)
            if row:
                results.append(_row_to_result(row))
            else:
                results.append({"success": False, "error": "Erro ao parsear linha CSV"})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    # Preencher se faltarem
    while len(results) < expected_count:
        results.append({"success": False, "error": "Resultado nao encontrado"})

    return results


def _row_to_result(row: dict) -> dict:
    """Converte uma linha CSV do SwissADME em dict estruturado."""
    def get_float(key, default=None):
        val = row.get(key, "")
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def get_bool(key):
        val = row.get(key, "").strip().lower()
        return val in ("yes", "high", "true")

    def get_str(key, default=""):
        return row.get(key, default).strip()

    return {
        "success": True,
        "source": "SwissADME",
        "physicochemical": {
            "formula": get_str("Formula"),
            "molecular_weight": get_float("MW"),
            "num_heavy_atoms": get_float("#Heavy atoms"),
            "num_arom_heavy_atoms": get_float("#Aromatic heavy atoms"),
            "fraction_csp3": get_float("Fraction Csp3"),
            "num_rotatable_bonds": get_float("#Rotatable bonds"),
            "num_h_bond_acceptors": get_float("#H-bond acceptors"),
            "num_h_bond_donors": get_float("#H-bond donors"),
            "molar_refractivity": get_float("MR"),
            "tpsa": get_float("TPSA"),
        },
        "lipophilicity": {
            "ilogp": get_float("iLOGP"),
            "xlogp3": get_float("XLOGP3"),
            "wlogp": get_float("WLOGP"),
            "mlogp": get_float("MLOGP"),
            "silicos_it": get_float("Silicos-IT Log P"),
            "consensus_logp": get_float("Consensus Log P"),
        },
        "solubility": {
            "log_s_esol": get_float("ESOL Log S"),
            "solubility_mg_ml": get_str("ESOL Solubility (mg/ml)"),
            "solubility_mol_l": get_str("ESOL Solubility (mol/l)"),
            "class_esol": get_str("ESOL Class"),
            "log_s_ali": get_float("Ali Log S"),
            "class_ali": get_str("Ali Class"),
        },
        "pharmacokinetics": {
            "gi_absorption": get_str("GI absorption"),
            "bbb_permeant": get_bool("BBB permeant"),
            "pgp_substrate": get_bool("Pgp substrate"),
            "cyp1a2_inhibitor": get_bool("CYP1A2 inhibitor"),
            "cyp2c19_inhibitor": get_bool("CYP2C19 inhibitor"),
            "cyp2c9_inhibitor": get_bool("CYP2C9 inhibitor"),
            "cyp2d6_inhibitor": get_bool("CYP2D6 inhibitor"),
            "cyp3a4_inhibitor": get_bool("CYP3A4 inhibitor"),
            "log_kp_skin": get_float("log Kp (cm/s)"),
        },
        "druglikeness": {
            "lipinski": f"{'Yes' if get_float('Lipinski #violations', 99) == 0 else 'No'}; {int(get_float('Lipinski #violations', 0))} violation(s)",
            "lipinski_pass": get_float("Lipinski #violations", 99) <= 1,
            "ghose": "Yes" if get_float("Ghose #violations", 99) == 0 else "No",
            "ghose_pass": get_float("Ghose #violations", 99) == 0,
            "veber": "Yes" if get_float("Veber #violations", 99) == 0 else "No",
            "veber_pass": get_float("Veber #violations", 99) == 0,
            "egan": "Yes" if get_float("Egan #violations", 99) == 0 else "No",
            "egan_pass": get_float("Egan #violations", 99) == 0,
            "muegge": "Yes" if get_float("Muegge #violations", 99) == 0 else "No",
            "muegge_pass": get_float("Muegge #violations", 99) == 0,
            "bioavailability_score": get_float("Bioavailability Score"),
        },
        "medicinal_chemistry": {
            "pains_alerts": f"{int(get_float('PAINS #alerts', 0))} alert",
            "brenk_alerts": f"{int(get_float('Brenk #alerts', 0))} alert",
            "leadlikeness": "Yes" if get_float("Leadlikeness #violations", 99) == 0 else f"No; {int(get_float('Leadlikeness #violations', 0))} violation(s)",
            "leadlikeness_pass": get_float("Leadlikeness #violations", 99) == 0,
            "synthetic_accessibility": get_float("Synthetic Accessibility"),
        },
    }
