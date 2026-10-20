import pytest

from app.models.loyalty import LoyaltyAccount
from app.models.transaction import CategoryEnum
from app.models.user import Family, RoleEnum, User
from app.services.loyalty_service import (
    POINTS_PER_BYN,
    award_cashback,
    award_points,
    cashback_for,
    convert_points_to_byn,
)


def _make_user(db, role: RoleEnum = RoleEnum.child, family=None) -> User:
    family = family or Family(name="Тестовая семья")
    if family.id is None:
        db.add(family)
        db.flush()
    user = User(
        login=f"user{db.query(User).count()}",
        password_hash="x",
        role=role,
        full_name="Тест Тестов",
        family_id=family.id,
    )
    db.add(user)
    db.flush()
    return user


# --- Кешбэк ------------------------------------------------------------------


def test_cashback_rate_is_5_percent():
    # 5% от 10 BYN = 0.5 BYN = 5 орешков (по 10 орешков на 1 BYN)
    assert cashback_for(CategoryEnum.food, 10.0) == 5
    assert cashback_for(CategoryEnum.sweets, 10.0) == 5
    assert cashback_for(CategoryEnum.education, 10.0) == 5
    assert cashback_for(CategoryEnum.entertainment, 10.0) == 5
    assert cashback_for(CategoryEnum.toys, 10.0) == 5


def test_cashback_not_granted_for_games_and_subscriptions():
    assert cashback_for(CategoryEnum.games, 50.0) == 0
    assert cashback_for(CategoryEnum.subscriptions, 50.0) == 0
    assert cashback_for(CategoryEnum.other, 50.0) == 0


def test_cashback_rounds_down_but_keeps_minimum_one_point():
    assert cashback_for(CategoryEnum.food, 0.5) == 1  # 0.25 орешка -> минимум 1
    assert cashback_for(CategoryEnum.food, 3.0) == 1  # 1.5 -> int() = 1
    assert cashback_for(CategoryEnum.food, 4.0) == 2  # 2.0 -> 2


def test_award_cashback_credits_account(db):
    user = _make_user(db)
    awarded = award_cashback(db, user.id, CategoryEnum.toys, 20.0)
    db.commit()

    assert awarded == 10
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user.id).one()
    assert account.points == 10


# --- Конвертация -------------------------------------------------------------


def test_convert_10_points_gives_1_byn(db):
    user = _make_user(db)
    award_points(db, user.id, 25, "Тест")
    db.commit()

    conversion = convert_points_to_byn(db, user.id, 10)
    db.commit()

    assert conversion.points_spent == 10
    assert conversion.byn_amount == 1

    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user.id).one()
    assert account.points == 15
    assert account.converted_byn == 1


def test_convert_requires_multiple_of_10(db):
    user = _make_user(db)
    award_points(db, user.id, 25, "Тест")
    db.commit()

    with pytest.raises(ValueError, match="кратное"):
        convert_points_to_byn(db, user.id, 7)


def test_convert_rejects_more_than_balance(db):
    user = _make_user(db)
    award_points(db, user.id, 5, "Тест")
    db.commit()

    with pytest.raises(ValueError, match="орешков"):
        convert_points_to_byn(db, user.id, 10)


def test_convert_rejects_non_positive(db):
    user = _make_user(db)
    with pytest.raises(ValueError):
        convert_points_to_byn(db, user.id, 0)
    with pytest.raises(ValueError):
        convert_points_to_byn(db, user.id, -10)


def test_points_per_byn_is_ten():
    assert POINTS_PER_BYN == 10


# --- Раздельные счета --------------------------------------------------------


def test_child_and_parent_have_separate_accounts(db):
    family = Family(name="Семья")
    db.add(family)
    db.flush()
    parent = _make_user(db, RoleEnum.parent, family)
    child = _make_user(db, RoleEnum.child, family)

    award_points(db, child.id, 30, "Квест")
    award_points(db, parent.id, 5, "Кешбэк")
    db.commit()

    child_account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == child.id).one()
    parent_account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == parent.id).one()

    assert child_account.points == 30
    assert parent_account.points == 5
