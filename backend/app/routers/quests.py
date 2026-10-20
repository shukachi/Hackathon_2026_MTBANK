from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_current_user
from app.db import get_db
from app.models.quest import Quest, QuestStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.quest import QuestCreateRequest, QuestOut
from app.services import loyalty_service

router = APIRouter(prefix="/quests", tags=["quests"])


def _assert_access(db: Session, child_id: int, user: User) -> None:
    if user.id == child_id:
        return
    if user.role == RoleEnum.parent:
        child = db.get(User, child_id)
        if child and child.family_id == user.family_id and child.role != RoleEnum.parent:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к квестам этого пользователя")


@router.get("", response_model=list[QuestOut])
def list_quests(child_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[QuestOut]:
    _assert_access(db, child_id, user)
    quests = db.query(Quest).filter(Quest.child_id == child_id).all()
    return [QuestOut.model_validate(q) for q in quests]


@router.post("", response_model=QuestOut)
def create_quest(
    payload: QuestCreateRequest, db: Session = Depends(get_db), parent: User = Depends(get_current_parent)
) -> QuestOut:
    child = db.get(User, payload.child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")

    quest = Quest(
        child_id=payload.child_id,
        title=payload.title,
        description=payload.description,
        reward_points=payload.reward_points,
        status=QuestStatusEnum.open,
        created_by=parent.id,
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return QuestOut.model_validate(quest)


@router.post("/{quest_id}/complete", response_model=QuestOut)
def complete_quest(quest_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> QuestOut:
    quest = db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Квест не найден")
    if quest.child_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только сам ребёнок может завершить свой квест")
    if quest.status == QuestStatusEnum.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Квест уже завершён")

    quest.status = QuestStatusEnum.completed
    quest.completed_at = datetime.now(timezone.utc)

    # Награда за квест идёт орешками на счёт ребёнка.
    if quest.reward_points > 0:
        loyalty_service.award_points(
            db, user.id, quest.reward_points, reason=f"Квест выполнен: {quest.title}"
        )

    db.commit()
    db.refresh(quest)
    return QuestOut.model_validate(quest)
