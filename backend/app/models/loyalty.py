from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class LoyaltyAccount(Base):
    """Счёт орешков пользователя.

    Баллы (орешки) ребёнка и родителя копятся РАЗДЕЛЬНО — у каждого свой счёт
    (ТЗ п.4.3: «Баллы накапливаются отдельно и ребёнком, и родителями»).

    `points` — текущий баланс орешков.
    `converted_byn` — деньги, полученные за конвертацию орешков (10 орешков = 1 BYN).
    """

    __tablename__ = "loyalty_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    converted_byn: Mapped[float] = mapped_column(Float, default=0.0)

    history: Mapped[list["LoyaltyHistory"]] = relationship(back_populates="account")
    conversions: Mapped[list["LoyaltyConversion"]] = relationship(back_populates="account")


class LoyaltyHistory(Base):
    """История начислений и списаний орешков (кешбэк, квесты, конвертация)."""

    __tablename__ = "loyalty_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("loyalty_accounts.id"), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    account: Mapped["LoyaltyAccount"] = relationship(back_populates="history")


class LoyaltyConversion(Base):
    """Операция конвертации орешков в рубли — аудит-трейл для ребёнка и родителя."""

    __tablename__ = "loyalty_conversions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("loyalty_accounts.id"), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    byn_amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    account: Mapped["LoyaltyAccount"] = relationship(back_populates="conversions")
