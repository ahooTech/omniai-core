# src/omniai/models/user.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Table, PrimaryKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization


# Define association table
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE")),
    Column("organization_id", String, ForeignKey("organizations.id", ondelete="CASCADE")),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),
    PrimaryKeyConstraint("user_id", "organization_id"),  # ← COMPOSITE PK
    Index(
        "idx_user_default_org",
        "user_id",
        unique=True,
        postgresql_where=Column("is_default")
    )
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: "usr_" + uuid.uuid4().hex
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users",
        lazy="selectin"
    )


"""
# Define association table
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", String, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),
    Index(
        "idx_user_default_org",
        "user_id",
        unique=True,
        postgresql_where=Column("is_default")
    )
)

"""