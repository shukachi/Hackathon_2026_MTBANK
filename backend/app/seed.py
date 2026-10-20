"""Демо-данные для хакатона. Запускать руками: `python -m app.seed`.
НЕ выполняется автоматически при старте сервера.
"""
import random
import sys
from datetime import datetime, timedelta, timezone

# На Windows консоль git bash/cmd часто использует cp1252/cp866, где кириллица
# ломается при print(). Принудительно переключаем stdout/stderr на UTF-8,
# чтобы финальный вывод логинов/паролей всегда печатался корректно.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.models.access_request import AccessRequest, AccessRequestStatusEnum
from app.models.card import Card, CardDesignEnum, CardStatusEnum
from app.models.goal import Goal
from app.models.limit import Limit, PeriodEnum
from app.models.loyalty import LoyaltyAccount
from app.models.quest import Quest, QuestStatusEnum
from app.models.transaction import CategoryEnum, Transaction, TransactionStatusEnum
from app.models.user import Family, RoleEnum, User
from app.services import loyalty_service

MERCHANTS_BY_CATEGORY = {
    CategoryEnum.food: ["Соседи", "Евроопт", "Школьная столовая"],
    CategoryEnum.sweets: ["Кондитерская", "Шоколадница", "Киоск у школы"],
    CategoryEnum.toys: ["Детский мир", "Игрушки.by"],
    CategoryEnum.games: ["Steam", "PlayStation Store", "Game Zone"],
    CategoryEnum.subscriptions: ["Netflix", "Spotify", "YouTube Premium"],
    CategoryEnum.education: ["Книжный магазин", "Онлайн-курс", "Школьные принадлежности"],
    CategoryEnum.entertainment: ["Кинотеатр Silver Screen", "Парк развлечений", "Боулинг"],
}

CATEGORY_AMOUNT_RANGE = {
    CategoryEnum.food: (3, 15),
    CategoryEnum.sweets: (2, 10),
    CategoryEnum.toys: (10, 60),
    CategoryEnum.games: (5, 40),
    CategoryEnum.subscriptions: (5, 20),
    CategoryEnum.education: (5, 30),
    CategoryEnum.entertainment: (10, 50),
}


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.login == "parent@moby.by").first()
        if existing:
            print("Seed уже выполнен ранее (найден parent@moby.by). Удалите app.db, чтобы пересоздать демо-данные.")
            return

        family = Family(name="Ивановы")
        db.add(family)
        db.flush()

        parent = User(
            login="parent@moby.by",
            password_hash=hash_password("Parent123!"),
            role=RoleEnum.parent,
            full_name="Иван Иванов",
            family_id=family.id,
        )
        db.add(parent)
        db.flush()

        anna = User(
            login="anna10",
            password_hash=hash_password("Child123!"),
            role=RoleEnum.child,
            full_name="Анна Иванова",
            age=10,
            family_id=family.id,
            parent_id=parent.id,
        )
        max_ = User(
            login="max16",
            password_hash=hash_password("Teen123!"),
            role=RoleEnum.teen,
            full_name="Максим Иванов",
            age=16,
            family_id=family.id,
            parent_id=parent.id,
        )
        db.add_all([anna, max_])
        db.flush()

        # У Анны две карты: основная и дополнительная «на мечту» — показываем,
        # что у ребёнка может быть несколько карт.
        anna_card = Card(user_id=anna.id, masked_number="**** **** **** 1001", status=CardStatusEnum.active, design=CardDesignEnum.child, balance=250.0)
        anna_extra_card = Card(user_id=anna.id, masked_number="**** **** **** 1002", status=CardStatusEnum.active, design=CardDesignEnum.child, balance=80.0)
        max_card = Card(user_id=max_.id, masked_number="**** **** **** 1602", status=CardStatusEnum.active, design=CardDesignEnum.teen, balance=180.0)
        db.add_all([anna_card, anna_extra_card, max_card])
        db.flush()

        anna_loyalty = LoyaltyAccount(user_id=anna.id, points=0)
        max_loyalty = LoyaltyAccount(user_id=max_.id, points=0)
        parent_loyalty = LoyaltyAccount(user_id=parent.id, points=0)
        db.add_all([anna_loyalty, max_loyalty, parent_loyalty])
        db.flush()

        # Транзакции за последние ~80 дней на обеих картах.
        now = datetime.now(timezone.utc)
        categories = list(MERCHANTS_BY_CATEGORY.keys())
        transactions = []
        for card, count in ((anna_card, 15), (max_card, 15)):
            for _ in range(count):
                category = random.choice(categories)
                merchant = random.choice(MERCHANTS_BY_CATEGORY[category])
                low, high = CATEGORY_AMOUNT_RANGE[category]
                amount = round(random.uniform(low, high), 2)
                days_ago = random.randint(0, 80)
                created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
                transactions.append(
                    Transaction(
                        card_id=card.id,
                        amount=amount,
                        category=category,
                        merchant=merchant,
                        status=TransactionStatusEnum.approved,
                        created_at=created_at,
                    )
                )
        db.add_all(transactions)
        db.flush()

        # Кешбэк орешками за уже совершённые операции — чтобы у ребёнка и подростка
        # был непустой счёт орешков сразу после сида. Орешки начисляются владельцу
        # карты, а не тому, кто совершил операцию: счёт у ребёнка и родителя раздельный.
        card_owner = {anna_card.id: anna.id, anna_extra_card.id: anna.id, max_card.id: max_.id}
        for tx in transactions:
            loyalty_service.award_cashback(db, card_owner[tx.card_id], tx.category, tx.amount)

        # Лимиты.
        db.add(Limit(child_id=anna.id, category=CategoryEnum.sweets, amount=50.0, period=PeriodEnum.week))
        db.add(Limit(child_id=max_.id, category=None, amount=200.0, period=PeriodEnum.month))

        # Квесты.
        quest1 = Quest(
            child_id=anna.id,
            title="Накопи 20 BYN за неделю",
            description="Отложи часть карманных денег и не трогай их 7 дней.",
            reward_points=50,
            status=QuestStatusEnum.open,
            created_by=parent.id,
        )
        quest2 = Quest(
            child_id=anna.id,
            title="Пройди урок финграмотности",
            description="Изучи урок 'Что такое бюджет' в приложении.",
            reward_points=30,
            status=QuestStatusEnum.completed,
            created_by=parent.id,
            completed_at=now - timedelta(days=5),
        )
        quest3 = Quest(
            child_id=max_.id,
            title="Сравни цены в трёх магазинах",
            description="Перед покупкой сравни цену минимум в 3 местах.",
            reward_points=40,
            status=QuestStatusEnum.open,
            created_by=parent.id,
        )
        db.add_all([quest1, quest2, quest3])

        # Начислим орешки за уже выполненный quest2.
        loyalty_service.award_points(db, anna.id, quest2.reward_points, reason=f"Квест выполнен: {quest2.title}")

        # У родителя тоже есть счёт орешков — свои баллы копятся отдельно от детских.
        loyalty_service.award_points(db, parent.id, 40, reason="Кешбэк 5% за покупки семьи")

        # Цели накопления.
        db.add(Goal(child_id=anna.id, title="Новый велосипед", target_amount=300.0, current_amount=75.0))
        db.add(Goal(child_id=max_.id, title="Наушники", target_amount=150.0, current_amount=40.0))

        # Pending access request от max16.
        db.add(AccessRequest(child_id=max_.id, feature="subscription", status=AccessRequestStatusEnum.pending))

        db.commit()

        print("\n=== Демо-данные созданы ===")
        print("Родитель:  login=parent@moby.by   password=Parent123!")
        print("Ребёнок:   login=anna10           password=Child123!   (Анна Иванова, 10 лет)")
        print("Подросток: login=max16             password=Teen123!    (Максим Иванов, 16 лет)")
        print("============================\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
