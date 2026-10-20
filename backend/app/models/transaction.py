import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CategoryEnum(str, enum.Enum):
    food = "food"
    sweets = "sweets"
    toys = "toys"
    games = "games"
    subscriptions = "subscriptions"
    education = "education"
    entertainment = "entertainment"
    other = "other"


class TransactionStatusEnum(str, enum.Enum):
    approved = "approved"
    blocked_by_limit = "blocked_by_limit"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[CategoryEnum] = mapped_column(Enum(CategoryEnum), nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TransactionStatusEnum] = mapped_column(
        Enum(TransactionStatusEnum), default=TransactionStatusEnum.approved
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
