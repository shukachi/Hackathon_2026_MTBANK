from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.card import Card
from app.models.qr_payment import QrPayment, QrPaymentStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.qr_payment import (
    CreateQrRequest,
    CreateQrResponse,
    PayQrRequest,
    PayQrResponse,
    QrPaymentOut,
)
from app.services import qr_service

router = APIRouter(prefix="/qr", tags=["qr-payments"])


def _assert_can_view(db: Session, user: User, target_user_id: int) -> None:
    if user.id == target_user_id:
        return
    if user.role == RoleEnum.parent:
        target = db.get(User, target_user_id)
        if target and target.family_id == user.family_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому QR-коду")


@router.post("/generate", response_model=CreateQrResponse)
def generate_qr(
    payload: CreateQrRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CreateQrResponse:
    """Генерация временного QR-кода (ребёнок / подросток).

    Выбирается категория покупки и карта, со счёта которой будут списаны
    средства при сканировании кода терминалом.
    """
    # Роль проверяем первым: родитель не должен получать QR для оплаты
    # даже со своей карты.
    if user.role not in (RoleEnum.child, RoleEnum.teen):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="QR для оплаты доступен только ребёнку и подростку",
        )

    card = db.get(Card, payload.card_id)
    if not card or card.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Карта не найдена или не принадлежит вам",
        )

    try:
        payment = qr_service.create_qr_payment(
            db,
            user=user,
            card=card,
            category=payload.category,
            amount=payload.amount,
            ttl_minutes=payload.ttl_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CreateQrResponse(
        token=payment.token,
        expires_at=payment.expires_at,
        payload=f"moby://pay/{payment.token}",
        ttl_minutes=payload.ttl_minutes,
    )


@router.get("/my", response_model=list[QrPaymentOut])
def list_my_qr(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[QrPaymentOut]:
    """Мои QR-коды: активные, оплаченные и истёкшие."""
    qr_service.expire_stale(db, user.id)
    rows = (
        db.query(QrPayment)
        .filter(QrPayment.user_id == user.id)
        .order_by(QrPayment.created_at.desc())
        .all()
    )
    return [QrPaymentOut.model_validate(r) for r in rows]


@router.post("/{token}/cancel", response_model=QrPaymentOut)
def cancel_qr(
    token: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QrPaymentOut:
    payment = db.query(QrPayment).filter(QrPayment.token == token).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR-код не найден")
    if payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Это не ваш QR-код")

    try:
        cancelled = qr_service.cancel_qr_payment(db, payment)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return QrPaymentOut.model_validate(cancelled)


@router.post("/{token}/pay", response_model=PayQrResponse)
def pay_qr(
    token: str,
    payload: PayQrRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PayQrResponse:
    """Оплата по QR (эмуляция терминала: сканирование кода в приложении)."""
    payment = db.query(QrPayment).filter(QrPayment.token == token).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR-код не найден")
    if payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Это не ваш QR-код")

    try:
        updated, transaction = qr_service.pay_qr_payment(
            db,
            payment,
            amount=payload.amount if payload else None,
            merchant=payload.merchant if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    card = db.get(Card, payment.card_id)
    return PayQrResponse(
        qr_payment=QrPaymentOut.model_validate(updated),
        transaction_id=transaction.id,
        debited_amount=transaction.amount,
        card_balance_left=card.balance,
    )


@router.get("/{token}", response_model=QrPaymentOut)
def get_qr(token: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> QrPaymentOut:
    payment = db.query(QrPayment).filter(QrPayment.token == token).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR-код не найден")
    _assert_can_view(db, user, payment.user_id)
    return QrPaymentOut.model_validate(payment)
