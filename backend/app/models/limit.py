import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.transaction import CategoryEnum


class PeriodEnum(str, enum.Enum):
    week = "week"
    month = "month"


class Limit(Base):
    __tablename__ = "limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[CategoryEnum | None] = mapped_column(Enum(CategoryEnum), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[PeriodEnum] = mapped_column(Enum(PeriodEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
