from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.card import Card
from app.models.transaction import CategoryEnum, Transaction, TransactionStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.card import CardOut
from app.schemas.transaction import SimulateTransactionRequest, SimulateTransactionResponse, TransactionOut
from app.services import limits_engine, loyalty_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _visible_child_ids(db: Session, user: User) -> list[int]:
    """Какие user_id транзакций может видеть текущий пользователь."""
    if user.role == RoleEnum.parent:
        children = db.query(User).filter(User.family_id == user.family_id, User.parent_id == user.id).all()
        return [c.id for c in children]
    return [user.id]


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    user_id: int | None = None,
    category: CategoryEnum | None = None,
    from_: datetime | None = None,
    to: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TransactionOut]:
    allowed_ids = _visible_child_ids(db, user)

    if user_id is not None:
        if user_id not in allowed_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к транзакциям этого пользователя")
        target_ids = [user_id]
    else:
        target_ids = allowed_ids

    query = db.query(Transaction).join(Card, Card.id == Transaction.card_id).filter(Card.user_id.in_(target_ids))

    if category is not None:
        query = query.filter(Transaction.category == category)
    if from_ is not None:
        query = query.filter(Transaction.created_at >= from_)
    if to is not None:
        query = query.filter(Transaction.created_at <= to)

    transactions = query.order_by(Transaction.created_at.desc()).all()
    return [TransactionOut.model_validate(t) for t in transactions]


@router.post("/simulate", response_model=SimulateTransactionResponse)
def simulate_transaction(
    payload: SimulateTransactionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulateTransactionResponse:
    card = db.get(Card, payload.card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Карта не найдена")

    allowed_ids = _visible_child_ids(db, user)
    if card.user_id not in allowed_ids and user.id != card.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой карте")

    blocked, reason = limits_engine.check_transaction(db, card.user_id, payload.category, payload.amount)

    transaction = Transaction(
        card_id=card.id,
        amount=payload.amount,
        category=payload.category,
        merchant=payload.merchant,
        status=TransactionStatusEnum.blocked_by_limit if blocked else TransactionStatusEnum.approved,
    )
    db.add(transaction)
    db.flush()

    # Кешбэк орешками начисляем только по одобренным операциям —
    # заблокированная лимитом покупка не должна приносить бонусы.
    cashback_points = 0
    insufficient_funds = False
    if not blocked:
        card.balance -= payload.amount
        # Баланс не блокирует покупку (единственный блокирующий механизм — лимит),
        # но о нехватке средств честно предупреждаем в ответе и в UI.
        insufficient_funds = card.balance < 0
        cashback_points = loyalty_service.award_cashback(db, card.user_id, payload.category, payload.amount)

    db.commit()
    db.refresh(transaction)
    db.refresh(card)

    return SimulateTransactionResponse(
        transaction=TransactionOut.model_validate(transaction),
        blocked=blocked,
        reason=reason,
        cashback_points=cashback_points,
        insufficient_funds=insufficient_funds,
        card=CardOut.model_validate(card),
    )
