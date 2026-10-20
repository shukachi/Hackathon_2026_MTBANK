from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_current_user
from app.db import get_db
from app.models.limit import Limit
from app.models.user import RoleEnum, User
from app.schemas.limit import LimitOut, LimitUpsertRequest

router = APIRouter(prefix="/limits", tags=["limits"])


def _assert_child_of_parent(db: Session, child_id: int, parent: User) -> User:
    child = db.get(User, child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")
    return child


@router.get("", response_model=list[LimitOut])
def list_limits(
    child_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[LimitOut]:
    if user.role == RoleEnum.parent:
        _assert_child_of_parent(db, child_id, user)
    elif user.id != child_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к лимитам другого пользователя")

    limits = db.query(Limit).filter(Limit.child_id == child_id).all()
    return [LimitOut.model_validate(limit) for limit in limits]


@router.put("", response_model=LimitOut)
def upsert_limit(
    payload: LimitUpsertRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> LimitOut:
    _assert_child_of_parent(db, payload.child_id, parent)

    limit = (
        db.query(Limit)
        .filter(Limit.child_id == payload.child_id, Limit.category == payload.category)
        .first()
    )
    if limit:
        limit.amount = payload.amount
        limit.period = payload.period
    else:
        limit = Limit(
            child_id=payload.child_id,
            category=payload.category,
            amount=payload.amount,
            period=payload.period,
        )
        db.add(limit)

    db.commit()
    db.refresh(limit)
    return LimitOut.model_validate(limit)
