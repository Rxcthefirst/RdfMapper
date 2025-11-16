"""Database models."""

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class Project(Base):
    """Project database model."""

    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="created")
    data_file = Column(String, nullable=True)
    ontology_file = Column(String, nullable=True)
    config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

