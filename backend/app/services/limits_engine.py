"""Проверка трат против активных лимитов ребёнка (по категории и по общему лимиту)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.limit import Limit, PeriodEnum
from app.models.transaction import CategoryEnum, Transaction, TransactionStatusEnum


def _period_start(period: PeriodEnum, now: datetime) -> datetime:
    if period == PeriodEnum.week:
        return now - timedelta(days=7)
    return now - timedelta(days=30)


def _spent_in_period(db: Session, child_id: int, category: CategoryEnum | None, period: PeriodEnum) -> float:
    now = datetime.now(timezone.utc)
    start = _period_start(period, now)

    query = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .join(Card, Card.id == Transaction.card_id)
        .filter(Card.user_id == child_id)
        .filter(Transaction.status == TransactionStatusEnum.approved)
        .filter(Transaction.created_at >= start)
    )
    if category is not None:
        query = query.filter(Transaction.category == category)

    return float(query.scalar() or 0.0)


def check_transaction(
    db: Session, child_id: int, category: CategoryEnum, amount: float
) -> tuple[bool, str | None]:
    """Возвращает (blocked, reason). blocked=True если сумма превышает хотя бы один активный лимит."""
    limits = db.query(Limit).filter(Limit.child_id == child_id).all()

    for limit in limits:
        # лимит применяется, если он общий (category is None) или совпадает с категорией транзакции
        if limit.category is not None and limit.category != category:
            continue

        already_spent = _spent_in_period(db, child_id, limit.category, limit.period)
        if already_spent + amount > limit.amount:
            scope = f"категории '{limit.category.value}'" if limit.category else "общему лимиту"
            reason = (
                f"Превышен лимит по {scope}: {limit.amount} BYN/{limit.period.value}. "
                f"Уже потрачено {already_spent:.2f} BYN, попытка потратить {amount:.2f} BYN."
            )
            return True, reason

    return False, None
