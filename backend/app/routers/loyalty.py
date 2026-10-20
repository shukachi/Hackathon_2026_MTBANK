from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.loyalty import LoyaltyAccount
from app.models.user import RoleEnum, User
from app.schemas.loyalty import (
    ConvertPointsRequest,
    ConvertPointsResponse,
    LoyaltyAccountOut,
)
from app.services import loyalty_service

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


def _account_out(account) -> LoyaltyAccountOut:
    """Собираем ответ с серверным курсом конвертации, чтобы UI не хардкодил 10."""
    out = LoyaltyAccountOut.model_validate(account)
    out.points_per_byn = loyalty_service.POINTS_PER_BYN
    return out


def _assert_can_view(db: Session, user: User, target_user_id: int) -> None:
    """Свой счёт видит всегда; чужой — только родитель своей семьи."""
    if user.id == target_user_id:
        return
    if user.role == RoleEnum.parent:
        target = db.get(User, target_user_id)
        if target and target.family_id == user.family_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому счёту лояльности")


@router.get("/{user_id}", response_model=LoyaltyAccountOut)
def get_loyalty(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> LoyaltyAccountOut:
    _assert_can_view(db, user, user_id)

    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт лояльности не найден")

    return _account_out(account)


@router.post("/convert", response_model=ConvertPointsResponse)
def convert_points(
    payload: ConvertPointsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConvertPointsResponse:
    """Конвертировать орешки в рубли: 10 орешков = 1 BYN."""
    try:
        conversion = loyalty_service.convert_points_to_byn(db, user.id, payload.points)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    account = loyalty_service.get_or_create_account(db, user.id)
    db.commit()
    db.refresh(account)
    db.refresh(conversion)

    return ConvertPointsResponse(
        points_spent=conversion.points_spent,
        byn_amount=conversion.byn_amount,
        points_left=account.points,
        converted_byn=account.converted_byn,
        account=_account_out(account),
    )
