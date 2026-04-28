from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes import proteins, molecules, analysis

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PharmaAI - Descoberta de Farmacos para Doencas Negligenciadas",
    description=(
        "Plataforma de IA para descoberta de novos farmacos com foco em Leishmaniose. "
        "Projeto vinculado a UFRN."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proteins.router)
app.include_router(molecules.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PharmaAI"}
