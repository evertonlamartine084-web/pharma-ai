from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    molecule_id = Column(Integer, ForeignKey("molecules.id"), nullable=False)
    protein_id = Column(Integer, ForeignKey("proteins.id"), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # validation, adme, docking
    results = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    binding_affinity = Column(Float, nullable=True)
    user_id = Column(String(100), default="default")
    created_at = Column(DateTime, server_default=func.now())
