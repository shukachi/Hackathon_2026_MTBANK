import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.card import Card


class QrPaymentStatusEnum(str, enum.Enum):
    active = "active"        # ждёт оплаты
    paid = "paid"            # оплачен
    expired = "expired"      # срок вышел
    cancelled = "cancelled"  # отменён ребёнком


class QrPayment(Base):
    """Временный QR для оплаты.

    Ребёнок (или подросток) выбирает категорию покупки и карту, со счёта которой
    будут списаны деньги, и получает QR-код. Код одноразовый и живёт ограниченное
    время: `expires_at`. При оплате с карты списываются средства, создаётся
    транзакция и начисляется кешбэк орешками — как при обычной покупке.
    """

    __tablename__ = "qr_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Токен из QR — по нему терминал находит платёж.
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    # Сумма может быть задана заранее, а может прийти от терминала при оплате.
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[QrPaymentStatusEnum] = mapped_column(Enum(QrPaymentStatusEnum), default=QrPaymentStatusEnum.active)
    merchant: Mapped[str] = mapped_column(String(255), default="Оплата по QR")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    card: Mapped[Card] = relationship()

    def is_expired(self, now: datetime | None = None) -> bool:
        """Истёк ли срок действия кода.

        SQLite отдаёт datetime без tzinfo, поэтому сравниваем в нормализованном
        UTC — иначе naive/aware-сравнение падает с TypeError.
        """
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return expires_at < now
