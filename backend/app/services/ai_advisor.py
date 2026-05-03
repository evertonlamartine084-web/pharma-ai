"""
Consultor IA para analise de moleculas.

Gera respostas baseadas em conhecimento farmacologico e nos dados
da molecula (validacao, ADME, docking, similaridade).
"""

from app.services.rdkit_service import validate_smiles
from app.services.adme_service import evaluate_adme


# Base de conhecimento farmacologico
KNOWLEDGE_BASE = {
    "lipinski": {
        "regra": "Regra dos 5 de Lipinski (Pfizer): MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10",
        "importancia": "Moleculas que violam mais de 1 regra tendem a ter baixa biodisponibilidade oral",
        "referencia": "Lipinski CA et al. 2001 Adv. Drug Deliv. Rev.",
    },
    "logp": {
        "ideal": "LogP entre 1 e 3 e ideal para absoracao oral",
        "alto": "LogP > 5 indica alta lipofilicidade, pode causar toxicidade e acumulo em tecidos",
        "baixo": "LogP < 0 indica molecula muito hidrofilica, dificuldade de atravessar membranas",
    },
    "tpsa": {
        "gi": "TPSA <= 140 A2 favorece absorcao gastrointestinal",
        "bbb": "TPSA <= 79 A2 favorece penetracao na barreira hematoencefalica",
        "oral": "TPSA entre 60-120 A2 e ideal para farmacos orais",
    },
    "solubilidade": {
        "esol": "Log S (ESOL) classifica: > -2 (soluvel), -2 a -4 (moderado), < -4 (pouco soluvel)",
        "importancia": "Solubilidade aquosa e essencial para absorcao e formulacao farmaceutica",
    },
    "docking": {
        "excelente": "Binding affinity <= -8 kcal/mol indica ligacao muito forte",
        "bom": "Binding affinity entre -6 e -8 kcal/mol indica boa afinidade",
        "moderado": "Binding affinity entre -4 e -6 kcal/mol requer otimizacao",
        "fraco": "Binding affinity > -4 kcal/mol indica ligacao fraca, improvavel atividade",
    },
    "cyp": {
        "importancia": "Inibicao de CYP450 pode causar interacoes medicamentosas perigosas",
        "cyp3a4": "CYP3A4 metaboliza ~50% dos farmacos do mercado",
        "cyp2d6": "CYP2D6 apresenta polimorfismo genetico significativo na populacao",
    },
    "pains": {
        "definicao": "PAINS (Pan Assay Interference Compounds) sao compostos que interferem em ensaios biologicos",
        "acao": "Moleculas com alertas PAINS devem ser avaliadas com cautela",
    },
    "sa_score": {
        "facil": "SA Score 1-4: sinteticamente acessivel, viavel para producao",
        "medio": "SA Score 4-6: moderadamente dificil, requer planejamento sintetico",
        "dificil": "SA Score > 6: sinteticamente desafiador, pode ser inviavel",
    },
    "leishmaniose": {
        "alvos": "Alvos validados incluem PTR1 (pteridine reductase), TryR (trypanothione reductase), CYP51",
        "farmacos": "Farmacos atuais: Miltefosina (unico oral), Anfotericina B, Paromomicina, Pentamidina",
        "desafios": "Resistencia crescente, toxicidade dos farmacos atuais, custo elevado",
    },
}


def analyze_molecule(smiles: str, adme_data: dict = None, docking_data: dict = None, question: str = None) -> dict:
    """Analisa molecula e responde perguntas com base no conhecimento farmacologico."""

    validation = validate_smiles(smiles)
    if not validation.get("valid"):
        return {"success": False, "error": "SMILES invalido"}

    adme = adme_data or evaluate_adme(smiles)

    # Gerar analise automatica
    insights = []
    recommendations = []
    warnings = []

    pc = adme.get("physicochemical", {})
    lp = adme.get("lipophilicity", {})
    sol = adme.get("solubility", {})
    pk = adme.get("pharmacokinetics", {})
    dl = adme.get("druglikeness", {})
    mc = adme.get("medicinal_chemistry", {})

    mw = pc.get("molecular_weight", 0)
    logp = lp.get("consensus_logp", validation.get("logp", 0))
    tpsa = pc.get("tpsa", validation.get("tpsa", 0))

    # Analise de drug-likeness
    if dl.get("lipinski_pass"):
        insights.append("A molecula passa na Regra de Lipinski, indicando potencial para administracao oral.")
    else:
        warnings.append(f"Violacoes de Lipinski detectadas. {KNOWLEDGE_BASE['lipinski']['importancia']}")

    # LogP
    if 1 <= logp <= 3:
        insights.append(f"LogP = {logp}: {KNOWLEDGE_BASE['logp']['ideal']}")
    elif logp > 5:
        warnings.append(f"LogP = {logp}: {KNOWLEDGE_BASE['logp']['alto']}")
        recommendations.append("Considerar adicionar grupos polares (OH, NH2) para reduzir LogP.")
    elif logp < 0:
        warnings.append(f"LogP = {logp}: {KNOWLEDGE_BASE['logp']['baixo']}")

    # TPSA
    gi = pk.get("gi_absorption", "")
    if gi == "High":
        insights.append(f"TPSA = {tpsa} A2: boa absorcao gastrointestinal prevista.")
    else:
        warnings.append(f"TPSA = {tpsa} A2: absorcao GI baixa. {KNOWLEDGE_BASE['tpsa']['gi']}")
        recommendations.append("Reduzir TPSA removendo grupos polares expostos ou formando ligacoes intramoleculares.")

    # Solubilidade
    log_s = sol.get("log_s_esol")
    if log_s is not None:
        if log_s >= -4:
            insights.append(f"Log S = {log_s}: solubilidade adequada para formulacao farmaceutica.")
        else:
            warnings.append(f"Log S = {log_s}: baixa solubilidade. {KNOWLEDGE_BASE['solubilidade']['importancia']}")
            recommendations.append("Considerar formas salinas ou co-cristais para melhorar solubilidade.")

    # CYP inhibition
    cyp_issues = []
    for cyp in ["cyp1a2_inhibitor", "cyp2c19_inhibitor", "cyp2c9_inhibitor", "cyp2d6_inhibitor", "cyp3a4_inhibitor"]:
        if pk.get(cyp):
            cyp_issues.append(cyp.replace("_inhibitor", "").upper())
    if cyp_issues:
        warnings.append(f"Inibicao de {', '.join(cyp_issues)} detectada. {KNOWLEDGE_BASE['cyp']['importancia']}")

    # SA Score
    sa = mc.get("synthetic_accessibility")
    if sa:
        if sa <= 4:
            insights.append(f"SA Score = {sa}: {KNOWLEDGE_BASE['sa_score']['facil']}")
        elif sa <= 6:
            insights.append(f"SA Score = {sa}: {KNOWLEDGE_BASE['sa_score']['medio']}")
        else:
            warnings.append(f"SA Score = {sa}: {KNOWLEDGE_BASE['sa_score']['dificil']}")

    # PAINS
    pains = mc.get("pains_alerts", "")
    if pains and "0 alert" not in pains:
        warnings.append(f"Alerta PAINS: {pains}. {KNOWLEDGE_BASE['pains']['acao']}")

    # Docking
    if docking_data:
        aff = docking_data.get("binding_affinity")
        if aff is not None:
            if aff <= -8:
                insights.append(f"Binding affinity = {aff} kcal/mol: {KNOWLEDGE_BASE['docking']['excelente']}")
            elif aff <= -6:
                insights.append(f"Binding affinity = {aff} kcal/mol: {KNOWLEDGE_BASE['docking']['bom']}")
            elif aff <= -4:
                warnings.append(f"Binding affinity = {aff} kcal/mol: {KNOWLEDGE_BASE['docking']['moderado']}")
            else:
                warnings.append(f"Binding affinity = {aff} kcal/mol: {KNOWLEDGE_BASE['docking']['fraco']}")

    # Responder pergunta especifica
    answer = None
    if question:
        answer = _answer_question(question, validation, adme, docking_data, insights, warnings, recommendations)

    # Score geral
    score = _calc_candidate_score(validation, adme, docking_data)

    return {
        "success": True,
        "insights": insights,
        "warnings": warnings,
        "recommendations": recommendations,
        "candidate_score": score,
        "answer": answer,
    }


def _answer_question(question: str, validation: dict, adme: dict, docking: dict, insights: list, warnings: list, recommendations: list) -> str:
    """Responde pergunta do usuario com base nos dados."""
    q = question.lower()

    if any(w in q for w in ["viavel", "candidato", "bom", "promissor"]):
        score = _calc_candidate_score(validation, adme, docking)
        if score >= 70:
            return f"Sim, esta molecula e um candidato promissor (score {score}/100). " + " ".join(insights[:2])
        elif score >= 40:
            return f"A molecula tem potencial moderado (score {score}/100) mas precisa de otimizacao. " + " ".join(warnings[:2])
        else:
            return f"A molecula tem baixo potencial (score {score}/100). Principais problemas: " + " ".join(warnings[:3])

    if any(w in q for w in ["solub", "dissol"]):
        sol = adme.get("solubility", {})
        return f"Solubilidade: Log S (ESOL) = {sol.get('log_s_esol', '?')} ({sol.get('class_esol', sol.get('class', '?'))}). {KNOWLEDGE_BASE['solubilidade']['importancia']}"

    if any(w in q for w in ["lipinski", "drug-like", "oral"]):
        dl = adme.get("druglikeness", {})
        return f"Drug-likeness: {dl.get('lipinski', '?')}. {KNOWLEDGE_BASE['lipinski']['regra']}"

    if any(w in q for w in ["dock", "afinidade", "ligacao", "binding"]):
        if docking:
            return f"Docking: {docking.get('binding_affinity', '?')} kcal/mol ({docking.get('classification', '?')}). Metodo: {docking.get('method', 'simulacao')}."
        return "Nenhum docking realizado para esta molecula ainda. Execute o docking na pagina de Avaliacoes."

    if any(w in q for w in ["cyp", "metabol", "interac"]):
        pk = adme.get("pharmacokinetics", {})
        cyps = [f"CYP{c}: {'Sim' if pk.get(f'cyp{c}_inhibitor') else 'Nao'}" for c in ["1a2", "2c19", "2c9", "2d6", "3a4"]]
        return f"Inibicao CYP: {', '.join(cyps)}. {KNOWLEDGE_BASE['cyp']['importancia']}"

    if any(w in q for w in ["sintet", "synth", "produz", "fabricar"]):
        sa = adme.get("medicinal_chemistry", {}).get("synthetic_accessibility")
        if sa:
            nivel = "facil" if sa <= 4 else "medio" if sa <= 6 else "dificil"
            return f"Synthetic Accessibility Score = {sa}. {KNOWLEDGE_BASE['sa_score'][nivel]}"
        return "SA Score nao disponivel."

    if any(w in q for w in ["leishman", "doenca", "alvo", "target"]):
        return f"{KNOWLEDGE_BASE['leishmaniose']['alvos']}. {KNOWLEDGE_BASE['leishmaniose']['farmacos']}. {KNOWLEDGE_BASE['leishmaniose']['desafios']}"

    if any(w in q for w in ["melhor", "otimiz", "recomen"]):
        if recommendations:
            return "Recomendacoes: " + " ".join(recommendations)
        return "A molecula parece estar bem otimizada. Considere realizar docking e testes in vitro."

    # Resposta generica
    return f"Analise geral: {len(insights)} pontos positivos, {len(warnings)} alertas. " + (insights[0] if insights else warnings[0] if warnings else "Execute ADME e Docking para mais detalhes.")


def _calc_candidate_score(validation: dict, adme: dict, docking: dict) -> int:
    """Calcula score de candidato (0-100)."""
    score = 50  # base

    # Validacao (+10)
    if validation.get("lipinski_pass"):
        score += 10

    # ADME
    dl = adme.get("druglikeness", {})
    if dl.get("lipinski_pass"):
        score += 5
    if dl.get("veber_pass"):
        score += 5
    if dl.get("ghose_pass"):
        score += 5

    pk = adme.get("pharmacokinetics", {})
    if pk.get("gi_absorption") == "High":
        score += 10
    if not pk.get("cyp3a4_inhibitor"):
        score += 3
    if not pk.get("cyp2d6_inhibitor"):
        score += 2

    mc = adme.get("medicinal_chemistry", {})
    pains = mc.get("pains_alerts", "")
    if "0 alert" in str(pains):
        score += 5

    sa = mc.get("synthetic_accessibility")
    if sa and sa <= 4:
        score += 5
    elif sa and sa > 6:
        score -= 10

    # Docking
    if docking:
        aff = docking.get("binding_affinity")
        if aff is not None:
            if aff <= -8:
                score += 15
            elif aff <= -6:
                score += 10
            elif aff <= -4:
                score += 5
            else:
                score -= 10

    return max(0, min(100, score))
