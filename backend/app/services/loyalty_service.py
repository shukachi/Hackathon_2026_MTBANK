"""Сервис лояльности: начисление и списание орешков, кешбэк, конвертация в рубли.

Единая точка правды по правилам программы:
- 1 орешек = 1 балл;
- 10 орешков = 1 BYN (конвертация);
- кешбэк начисляется на операции в «семейных» категориях: 5% от суммы,
  но не меньше 1 орешка за операцию (иначе копейки не набегают);
- орешки копятся отдельно у ребёнка и у родителя (ТЗ п.4.3).
"""
from sqlalchemy.orm import Session

from app.models.loyalty import LoyaltyAccount, LoyaltyConversion, LoyaltyHistory
from app.models.transaction import CategoryEnum

# Сколько орешков стоит 1 BYN при конвертации.
POINTS_PER_BYN = 10

# Кешбэк в долях: 0.05 = 5% от суммы операции.
CASHBACK_RATE = 0.05

# Категории с кешбэком. Игры и подписки исключены осознанно: это «серые» зоны
# трат, которые родитель ограничивает лимитами, а не поощряет бонусами.
CASHBACK_CATEGORIES: frozenset[CategoryEnum] = frozenset(
    {
        CategoryEnum.food,
        CategoryEnum.sweets,
        CategoryEnum.education,
        CategoryEnum.entertainment,
        CategoryEnum.toys,
    }
)


def get_or_create_account(db: Session, user_id: int) -> LoyaltyAccount:
    """Возвращает счёт орешков пользователя, создавая его при первом обращении."""
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if account is None:
        account = LoyaltyAccount(user_id=user_id, points=0, converted_byn=0.0)
        db.add(account)
        db.flush()
    return account


def award_points(db: Session, user_id: int, points: int, reason: str) -> LoyaltyAccount:
    """Начислить орешки и записать это в историю."""
    if points <= 0:
        raise ValueError("Количество орешков должно быть положительным")

    account = get_or_create_account(db, user_id)
    account.points += points
    db.add(LoyaltyHistory(account_id=account.id, delta=points, reason=reason))
    return account


def cashback_for(category: CategoryEnum, amount: float) -> int:
    """Сколько орешков даёт операция в этой категории. 0 — если кешбэка нет."""
    if category not in CASHBACK_CATEGORIES or amount <= 0:
        return 0
    # Минимум 1 орешек за операцию: иначе копейки не копятся и кешбэк не виден.
    return max(1, int(amount * CASHBACK_RATE * POINTS_PER_BYN))


def award_cashback(db: Session, user_id: int, category: CategoryEnum, amount: float) -> int:
    """Начислить кешбэк орешками за операцию. Возвращает начисленное количество."""
    points = cashback_for(category, amount)
    if points == 0:
        return 0
    award_points(
        db,
        user_id,
        points,
        reason=f"Кешбэк 5% за покупку ({category.value})",
    )
    return points


def convert_points_to_byn(db: Session, user_id: int, points: int) -> LoyaltyConversion:
    """Списать орешки и зачислить деньги на счёт пользователя.

    Требуется кратное 10 орешков (1 BYN) и достаточно орешков на счёте.
    """
    if points <= 0:
        raise ValueError("Количество орешков должно быть положительным")
    if points % POINTS_PER_BYN != 0:
        raise ValueError(f"Конвертировать можно кратное {POINTS_PER_BYN} орешков")

    account = get_or_create_account(db, user_id)
    if account.points < points:
        raise ValueError(f"На счёте только {account.points} орешков")

    byn_amount = points // POINTS_PER_BYN
    account.points -= points
    account.converted_byn += byn_amount

    db.add(LoyaltyHistory(account_id=account.id, delta=-points, reason=f"Конвертация {points} орешков в {byn_amount} BYN"))
    conversion = LoyaltyConversion(account_id=account.id, points_spent=points, byn_amount=byn_amount)
    db.add(conversion)
    return conversion
