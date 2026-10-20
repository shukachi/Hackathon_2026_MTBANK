"""Простой RAG без векторной БД: keyword-пересечение сообщения ребёнка
с последними транзакциями (категория/merchant), чтобы сформировать контекст
для LLM и/или rule-based fallback-ответ.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.transaction import CategoryEnum, Transaction

RECENT_TRANSACTIONS_LIMIT = 10
FALLBACK_LOOKBACK_DAYS = 30

# Ключевые слова (ru) -> категория. Используются и для RAG-контекста, и для rule-based ответа.
CATEGORY_KEYWORDS: dict[CategoryEnum, list[str]] = {
    CategoryEnum.food: ["еда", "еду", "кушать", "обед", "продукт", "food"],
    CategoryEnum.sweets: ["сладост", "конфет", "шоколад", "sweets"],
    CategoryEnum.toys: ["игрушк", "toys"],
    CategoryEnum.games: ["игры", "игра", "игровые", "games"],
    CategoryEnum.subscriptions: ["подпис", "subscriptions"],
    CategoryEnum.education: ["учеб", "образован", "книг", "education"],
    CategoryEnum.entertainment: ["развлечен", "кино", "парк", "entertainment"],
    CategoryEnum.other: ["other"],
}


def match_categories(message: str) -> list[CategoryEnum]:
    lowered = message.lower()
    matched = [cat for cat, keywords in CATEGORY_KEYWORDS.items() if any(kw in lowered for kw in keywords)]
    return matched


def get_recent_transactions(db: Session, user_id: int, limit: int = RECENT_TRANSACTIONS_LIMIT) -> list[Transaction]:
    return (
        db.query(Transaction)
        .join(Card, Card.id == Transaction.card_id)
        .filter(Card.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


def build_context(db: Session, user_id: int, message: str) -> tuple[str, list[CategoryEnum]]:
    """Возвращает (текстовый контекст для LLM, список совпавших категорий)."""
    matched_categories = match_categories(message)
    recent = get_recent_transactions(db, user_id)

    lines = [
        f"- {t.created_at.date()} {t.category.value} {t.merchant}: {t.amount} BYN ({t.status.value})"
        for t in recent
    ]
    context = "Последние транзакции пользователя:\n" + "\n".join(lines) if lines else "Транзакций пока нет."
    return context, matched_categories


def spent_by_categories(db: Session, user_id: int, categories: list[CategoryEnum], days: int = FALLBACK_LOOKBACK_DAYS) -> float:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = (
        db.query(Transaction)
        .join(Card, Card.id == Transaction.card_id)
        .filter(Card.user_id == user_id)
        .filter(Transaction.created_at >= since)
    )
    if categories:
        query = query.filter(Transaction.category.in_(categories))
    return sum(t.amount for t in query.all())
