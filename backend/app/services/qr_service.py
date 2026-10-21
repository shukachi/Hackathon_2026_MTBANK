"""Сервис временных QR-платежей.

Один QR — одна оплата. Код живёт ограниченное время (`QR_TTL_MINUTES`), после чего
помечается истёкшим. Оплата списывает средства с выбранной карты, создаёт обычную
транзакцию (с кешбэком орешками) и переводит QR в статус «оплачен».
"""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.qr_payment import QrPayment, QrPaymentStatusEnum
from app.models.transaction import CategoryEnum, Transaction, TransactionStatusEnum
from app.models.user import RoleEnum, User
from app.services import loyalty_service

# Сколько живёт QR-код.
QR_TTL_MINUTES = 10

# Сколько QR может быть активно одновременно у одного ребёнка.
MAX_ACTIVE_QR = 5


def _generate_token() -> str:
    """Короткий токен, который терминал распознаёт из QR-кода."""
    return secrets.token_urlsafe(16)


def create_qr_payment(
    db: Session,
    user: User,
    card: Card,
    category: CategoryEnum,
    amount: float | None = None,
    ttl_minutes: int = QR_TTL_MINUTES,
) -> QrPayment:
    """Создаёт временный QR для ребёнка/подростка."""
    if user.role not in (RoleEnum.child, RoleEnum.teen):
        raise ValueError("QR для оплаты доступен только ребёнку и подростку")
    if card.user_id != user.id:
        raise ValueError("Карта принадлежит другому пользователю")
    if amount is not None and amount <= 0:
        raise ValueError("Сумма оплаты должна быть больше нуля")

    # Не плодим активные коды: старые гасим.
    expire_stale(db, user.id)
    active = (
        db.query(QrPayment)
        .filter(QrPayment.user_id == user.id, QrPayment.status == QrPaymentStatusEnum.active)
        .count()
    )
    if active >= MAX_ACTIVE_QR:
        raise ValueError(f"Слишком много активных QR-кодов (максимум {MAX_ACTIVE_QR}). Отмените один из них.")

    now = datetime.now(timezone.utc)
    payment = QrPayment(
        token=_generate_token(),
        user_id=user.id,
        card_id=card.id,
        category=category.value,
        amount=amount,
        status=QrPaymentStatusEnum.active,
        expires_at=now + timedelta(minutes=ttl_minutes),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def expire_stale(db: Session, user_id: int | None = None) -> int:
    """Помечает истёкшие активные коды. Возвращает количество."""
    now = datetime.now(timezone.utc)
    query = db.query(QrPayment).filter(QrPayment.status == QrPaymentStatusEnum.active)
    if user_id is not None:
        query = query.filter(QrPayment.user_id == user_id)

    expired = 0
    for payment in query.all():
        if payment.is_expired(now):
            payment.status = QrPaymentStatusEnum.expired
            expired += 1
    if expired:
        db.commit()
    return expired


def cancel_qr_payment(db: Session, payment: QrPayment) -> QrPayment:
    """Ребёнок отменяет свой QR — код больше не сработает."""
    if payment.status != QrPaymentStatusEnum.active:
        raise ValueError("Отменить можно только активный QR-код")
    payment.status = QrPaymentStatusEnum.cancelled
    db.commit()
    db.refresh(payment)
    return payment


def pay_qr_payment(
    db: Session,
    payment: QrPayment,
    amount: float | None = None,
    merchant: str = "Оплата по QR",
) -> tuple[QrPayment, Transaction]:
    """Проводит оплату по QR: списывает средства с карты и создаёт транзакцию."""
    now = datetime.now(timezone.utc)

    if payment.status == QrPaymentStatusEnum.paid:
        raise ValueError("QR-код уже использован")
    if payment.status == QrPaymentStatusEnum.cancelled:
        raise ValueError("QR-код отменён")
    if payment.is_expired(now):
        payment.status = QrPaymentStatusEnum.expired
        db.commit()
        raise ValueError("Срок действия QR-кода истёк")

    final_amount = amount if amount is not None else payment.amount
    if final_amount is None or final_amount <= 0:
        raise ValueError("Не указана сумма оплаты")

    card = db.get(Card, payment.card_id)
    if not card:
        raise ValueError("Карта не найдена")

    # В БД категория лежит строкой — приводим к enum, как и остальной код.
    category = CategoryEnum(payment.category)

    transaction = Transaction(
        card_id=card.id,
        amount=final_amount,
        category=category,
        merchant=merchant or payment.merchant,
        status=TransactionStatusEnum.approved,
    )
    db.add(transaction)
    db.flush()

    card.balance -= final_amount
    payment.amount = final_amount
    payment.status = QrPaymentStatusEnum.paid
    payment.paid_at = now
    payment.merchant = merchant or payment.merchant

    # Кешбэк орешками — как при обычной покупке, владельцу карты.
    loyalty_service.award_cashback(db, card.user_id, category, final_amount)

    db.commit()
    db.refresh(payment)
    db.refresh(transaction)
    return payment, transaction
