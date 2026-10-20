import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_current_user
from app.db import get_db
from app.models.card import Card, CardDesignEnum, CardStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.card import CardOut, IssueCardRequest, TopUpCardRequest

router = APIRouter(prefix="/cards", tags=["cards"])


def _generate_masked_number() -> str:
    last4 = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"**** **** **** {last4}"


def _design_for_age(age: int | None) -> CardDesignEnum:
    return CardDesignEnum.teen if age is not None and age >= 14 else CardDesignEnum.child


@router.get("", response_model=list[CardOut])
def list_cards(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CardOut]:
    """Все карты пользователя. У ребёнка их может быть несколько.

    Без `user_id` — карты текущего пользователя. С `user_id` — карты указанного
    ребёнка: доступно самому ребёнку и родителю своей семьи.
    """
    if user_id is None or user_id == user.id:
        target_id = user.id
    else:
        if user.role != RoleEnum.parent:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к картам этого пользователя")
        owner = db.get(User, user_id)
        if not owner or owner.family_id != user.family_id or owner.role == RoleEnum.parent:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к картам этого пользователя")
        target_id = user_id

    cards = db.query(Card).filter(Card.user_id == target_id).order_by(Card.created_at.asc()).all()
    return [CardOut.model_validate(c) for c in cards]


@router.get("/me", response_model=CardOut)
def get_my_card(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CardOut:
    """Первая (основная) карта текущего пользователя — чтобы не требовать card_id с фронтенда."""
    card = db.query(Card).filter(Card.user_id == user.id).order_by(Card.created_at.asc()).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="У пользователя нет карты")
    return CardOut.model_validate(card)


def _get_card_or_404(db: Session, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Карта не найдена")
    return card


def _check_access(db: Session, card: Card, user: User) -> None:
    if user.id == card.user_id:
        return
    if user.role == RoleEnum.parent:
        owner = db.get(User, card.user_id)
        if owner is not None and owner.family_id == user.family_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой карте")


@router.get("/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CardOut:
    card = _get_card_or_404(db, card_id)
    _check_access(db, card, user)
    return CardOut.model_validate(card)


@router.post("", response_model=CardOut)
def issue_card(
    payload: IssueCardRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> CardOut:
    """Выпустить дополнительную карту ребёнку от имени родителя.

    У ребёнка может быть несколько карт — например, основная и отдельная
    накопительная под цель. Родитель также может задать стартовый баланс
    (карманные деньги).
    """
    child = db.get(User, payload.child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")

    card = Card(
        user_id=child.id,
        masked_number=_generate_masked_number(),
        status=CardStatusEnum.active,
        design=payload.design or _design_for_age(child.age),
        balance=payload.balance,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.post("/{card_id}/top-up", response_model=CardOut)
def top_up_card(
    card_id: int,
    payload: TopUpCardRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> CardOut:
    """Пополнить баланс карты ребёнка (перевод карманных денег от родителя)."""
    card = _get_card_or_404(db, card_id)
    owner = db.get(User, card.user_id)
    if not owner or owner.family_id != parent.family_id or owner.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Карта не принадлежит вашей семье")

    card.balance += payload.amount
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.post("/{card_id}/block", response_model=CardOut)
def block_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CardOut:
    card = _get_card_or_404(db, card_id)
    _check_access(db, card, user)
    card.status = CardStatusEnum.blocked
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.post("/{card_id}/unblock", response_model=CardOut)
def unblock_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CardOut:
    card = _get_card_or_404(db, card_id)
    _check_access(db, card, user)
    card.status = CardStatusEnum.active
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)
