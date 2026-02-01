# src/omniai/models/invite.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, ForeignKey
import datetime as dt
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User

class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: "inv_" + uuid.uuid4().hex
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    invited_by_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )
    expires_at: Mapped[dt.datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)
    )
    
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (optional for now)
    # organization: Mapped["Organization"] = relationship()
    # invited_by: Mapped["User"] = relationship()

    

