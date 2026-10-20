from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.card import Card, CardStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.card import CardOut

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/me", response_model=CardOut)
def get_my_card(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CardOut:
    """Карта текущего пользователя (ребёнка/подростка) — чтобы не требовать card_id с фронтенда."""
    card = db.query(Card).filter(Card.user_id == user.id).first()
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
