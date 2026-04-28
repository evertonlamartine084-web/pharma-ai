from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Molecule(Base):
    __tablename__ = "molecules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    smiles = Column(Text, nullable=False)
    target_protein_id = Column(Integer, ForeignKey("proteins.id"), nullable=True)
    source = Column(String(50), default="manual")  # manual, generated, csv
    is_valid = Column(Boolean, default=None, nullable=True)
    molecular_weight = Column(Float, nullable=True)
    logp = Column(Float, nullable=True)
    hbd = Column(Integer, nullable=True)  # hydrogen bond donors
    hba = Column(Integer, nullable=True)  # hydrogen bond acceptors
    lipinski_pass = Column(Boolean, nullable=True)
    user_id = Column(String(100), default="default")
    created_at = Column(DateTime, server_default=func.now())
