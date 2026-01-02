import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Table, func
from sqlalchemy.orm import relationship

from .organization import Base

user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("organization_id", String, ForeignKey("organizations.id"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),
    # ✅ Enforce one default org per user (PostgreSQL only)
    Index(
        "idx_user_default_org",
        "user_id",
        unique=True,
        postgresql_where=Column("is_default")
    )
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: "usr_" + str(uuid.uuid4()).replace("-", ""))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organizations = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users"
    )
