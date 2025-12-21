# src/omniai/models/user.py
import uuid
from sqlalchemy import String, Column, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .organization import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: "usr_" + str(uuid.uuid4()).replace("-", ""))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="users")