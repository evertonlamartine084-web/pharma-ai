from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Protein(Base):
    __tablename__ = "proteins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organism = Column(String(255), default="Leishmania")
    sequence = Column(Text, nullable=True)
    pdb_data = Column(Text, nullable=True)
    source = Column(String(50), default="manual")  # manual, alphafold, upload
    user_id = Column(String(100), default="default")
    created_at = Column(DateTime, server_default=func.now())
