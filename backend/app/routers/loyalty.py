from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.loyalty import LoyaltyAccount
from app.models.user import RoleEnum, User
from app.schemas.loyalty import LoyaltyAccountOut

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.get("/{user_id}", response_model=LoyaltyAccountOut)
def get_loyalty(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> LoyaltyAccountOut:
    if user.id != user_id:
        if user.role != RoleEnum.parent:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому счёту лояльности")
        target = db.get(User, user_id)
        if not target or target.family_id != user.family_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому счёту лояльности")

    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт лояльности не найден")

    return LoyaltyAccountOut.model_validate(account)
