import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AccessRequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    feature: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AccessRequestStatusEnum] = mapped_column(
        Enum(AccessRequestStatusEnum), default=AccessRequestStatusEnum.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
