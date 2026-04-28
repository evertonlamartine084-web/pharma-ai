# PharmaAI - Descoberta de Farmacos para Doencas Negligenciadas

Plataforma de inteligencia artificial para descoberta de novos farmacos com foco em **Leishmaniose**.
Projeto vinculado a Universidade Federal do Rio Grande do Norte (UFRN).

## Arquitetura

```
INPUT (PDB/SMILES) -> Geracao IA -> RDKit (validacao) -> ADME (farmacocinetica) -> Docking -> OUTPUT
```

### Backend (Python/FastAPI)
- **RDKit**: Validacao quimica real (Lipinski, peso molecular, logP, TPSA)
- **AlphaFold API**: Busca de estruturas proteicas via UniProt ID
- **ADME**: Calculos farmacocieneticos baseados em RDKit (solubilidade ESOL, permeabilidade, drug-likeness)
- **Docking**: Simulacao de binding affinity baseada em propriedades moleculares
- **Gerador IA**: Geracao de novas moleculas via mutacao, fusao de fragmentos e scaffold hopping

### Frontend (React/Tailwind)
- Dashboard com estatisticas
- Upload de proteinas (PDB) e sequencias FASTA
- Integracao AlphaFold para busca de estruturas
- Input de SMILES manual e CSV
- Geracao de moleculas com IA
- Visualizacao 3D de proteinas (3Dmol.js)
- Pipeline completo de analise (Validacao + ADME + Docking)
- Historico de analises
- Exportacao JSON/CSV

## Execucao Local

### Requisitos
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend disponivel em: http://localhost:8000
Documentacao API: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponivel em: http://localhost:5173

### Docker

```bash
docker-compose up --build
```

## Endpoints da API

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | /api/proteins/ | Listar proteinas |
| POST | /api/proteins/upload-pdb | Upload de arquivo PDB |
| POST | /api/proteins/sequence | Adicionar sequencia FASTA |
| POST | /api/proteins/alphafold | Buscar estrutura no AlphaFold |
| POST | /api/proteins/seed-leishmania | Popular banco com proteinas de Leishmania |
| GET | /api/molecules/ | Listar moleculas |
| POST | /api/molecules/add | Adicionar SMILES |
| POST | /api/molecules/upload-csv | Importar CSV |
| POST | /api/molecules/generate | Gerar moleculas com IA |
| POST | /api/molecules/seed | Popular banco com moleculas conhecidas |
| POST | /api/molecules/export | Exportar moleculas (JSON/CSV) |
| POST | /api/analysis/validate/{id} | Validacao RDKit |
| POST | /api/analysis/adme/{id} | Avaliacao ADME |
| POST | /api/analysis/docking | Docking molecular |
| POST | /api/analysis/pipeline/{id} | Pipeline completo |

## Banco de Dados Inicial

### Proteinas de Leishmania
- **PTR1** (Pteridine reductase 1) - L. major - Alvo terapeutico validado
- **TryR** (Trypanothione reductase) - L. infantum - Enzima essencial

### Moleculas Conhecidas
- Miltefosina (unico farmaco oral aprovado)
- Anfotericina B
- Paromomicina
- Sitamaquina
- Pentamidina

## Melhorias Futuras

1. **IA Generativa Avancada**: Integrar modelos Transformer (MolGPT, ChemBERTa) para geracao mais sofisticada
2. **AutoDock Vina**: Substituir simulacao por docking real via linha de comando
3. **UCSF ChimeraX**: Integracao via REST API do ChimeraX para visualizacao avancada
4. **SwissADME real**: Web scraping ou integracao quando API estiver disponivel
5. **Autenticacao**: Sistema de usuarios com JWT
6. **PostgreSQL**: Migrar de SQLite para banco de producao
7. **Celery + Redis**: Filas para tarefas pesadas (docking, geracao)
8. **ML de Atividade**: Modelo preditivo de atividade anti-Leishmania
9. **Integracao PubChem/ChEMBL**: Importar dados de atividade biologica
10. **Deploy Cloud**: Containerizacao completa com CI/CD
