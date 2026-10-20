from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_current_user
from app.db import get_db
from app.models.access_request import AccessRequest, AccessRequestStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.access_request import AccessRequestCreateRequest, AccessRequestDecideRequest, AccessRequestOut

router = APIRouter(prefix="/access-requests", tags=["access_requests"])


@router.post("", response_model=AccessRequestOut)
def create_access_request(
    payload: AccessRequestCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> AccessRequestOut:
    if user.role not in (RoleEnum.child, RoleEnum.teen):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только ребёнок может создать запрос доступа")

    request = AccessRequest(child_id=user.id, feature=payload.feature, status=AccessRequestStatusEnum.pending)
    db.add(request)
    db.commit()
    db.refresh(request)
    return AccessRequestOut.model_validate(request)


@router.get("", response_model=list[AccessRequestOut])
def list_access_requests(
    family_id: int, db: Session = Depends(get_db), parent: User = Depends(get_current_parent)
) -> list[AccessRequestOut]:
    if family_id != parent.family_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к запросам другой семьи")

    child_ids = [u.id for u in db.query(User).filter(User.family_id == family_id, User.role != RoleEnum.parent).all()]
    requests = db.query(AccessRequest).filter(AccessRequest.child_id.in_(child_ids)).all()
    return [AccessRequestOut.model_validate(r) for r in requests]


@router.post("/{request_id}/decide", response_model=AccessRequestOut)
def decide_access_request(
    request_id: int,
    payload: AccessRequestDecideRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> AccessRequestOut:
    request = db.get(AccessRequest, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запрос не найден")

    child = db.get(User, request.child_id)
    if not child or child.family_id != parent.family_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому запросу")

    request.status = AccessRequestStatusEnum(payload.decision)
    request.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)
    return AccessRequestOut.model_validate(request)
