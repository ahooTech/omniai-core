# src/omniai/models/user.py
import uuid
from sqlalchemy import String, Column, DateTime, Boolean, Table, ForeignKey, func
from sqlalchemy.orm import relationship
from .organization import Base

# 🔗 Join table: connects users to organizations
# Tracks: membership, default org, and role (owner/member)
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("organization_id", String, ForeignKey("organizations.id"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),  # ← NEW: "owner" or "member"
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: "usr_" + str(uuid.uuid4()).replace("-", ""))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 🔄 Link to organizations via the join table
    organizations = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users"
    )