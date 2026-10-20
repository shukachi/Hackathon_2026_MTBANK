import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CardStatusEnum(str, enum.Enum):
    active = "active"
    blocked = "blocked"


class CardDesignEnum(str, enum.Enum):
    child = "child"
    teen = "teen"
    adult = "adult"


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    masked_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[CardStatusEnum] = mapped_column(Enum(CardStatusEnum), default=CardStatusEnum.active)
    design: Mapped[CardDesignEnum] = mapped_column(Enum(CardDesignEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
