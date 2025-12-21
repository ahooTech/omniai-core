# src/omniai/models/organization.py
from sqlalchemy import String, Column, DateTime, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: "org_" + str(uuid.uuid4()).replace("-", ""))
    name = Column(String, nullable=False, index=True)  # e.g., "Ministry of Agriculture - Nigeria"
    slug = Column(String, unique=True, nullable=False, index=True)  # e.g., "agri-ng" (for URLs/subdomains)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(2), nullable=True)  # e.g., "NG", "KE"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", back_populates="organization")