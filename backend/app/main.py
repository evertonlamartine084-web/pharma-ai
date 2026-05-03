from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.routes import proteins, molecules, analysis, auth, similarity, report, advisor

Base.metadata.create_all(bind=engine)

# Criar usuario demo automaticamente se nao existir (evita perda no Render free)
def _seed_demo_user():
    from app.models.user import User
    from app.services.auth_service import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "demo").first():
            db.add(User(
                username="demo",
                email="demo@pharmaai.app",
                hashed_password=hash_password("demo123"),
                full_name="Pesquisador",
                institution="UFRN",
            ))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

_seed_demo_user()

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(proteins.router)
app.include_router(molecules.router)
app.include_router(analysis.router)
app.include_router(similarity.router)
app.include_router(report.router)
app.include_router(advisor.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PharmaAI"}
