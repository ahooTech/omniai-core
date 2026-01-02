
"""
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
"""

# src/omniai/models/organization.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User  # for type checker onl


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=lambda: "org_" + uuid.uuid4().hex
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_organization",
        back_populates="organizations",
        lazy="selectin"
    )