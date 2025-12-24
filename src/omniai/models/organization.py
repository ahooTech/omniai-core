# src/omniai/models/organization.py
import uuid
import re
from sqlalchemy import String, Column, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: "org_" + str(uuid.uuid4()).replace("-", ""))
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 🔄 Link back to users
    users = relationship(
        "User",
        secondary="user_organization",  # ← matches table name above
        back_populates="organizations"
    )