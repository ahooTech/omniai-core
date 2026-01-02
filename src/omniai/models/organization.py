# src/omniai/models/organization.py
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.orm import declarative_base, relationship  # ✅ FIXED IMPORT

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: "org_" + str(uuid.uuid4()).replace("-", ""))
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship(
        "User",
        secondary="user_organization",
        back_populates="organizations"
    )
