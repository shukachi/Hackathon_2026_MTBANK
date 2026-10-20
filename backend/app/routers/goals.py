from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.goal import Goal
from app.models.user import RoleEnum, User
from app.schemas.goal import GoalContributeRequest, GoalCreateRequest, GoalOut

router = APIRouter(prefix="/goals", tags=["goals"])


def _assert_access(db: Session, child_id: int, user: User) -> None:
    if user.id == child_id:
        return
    if user.role == RoleEnum.parent:
        child = db.get(User, child_id)
        if child and child.family_id == user.family_id and child.role != RoleEnum.parent:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к целям этого пользователя")


@router.get("", response_model=list[GoalOut])
def list_goals(child_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[GoalOut]:
    _assert_access(db, child_id, user)
    goals = db.query(Goal).filter(Goal.child_id == child_id).all()
    return [GoalOut.model_validate(g) for g in goals]


@router.post("", response_model=GoalOut)
def create_goal(
    payload: GoalCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> GoalOut:
    _assert_access(db, payload.child_id, user)
    goal = Goal(child_id=payload.child_id, title=payload.title, target_amount=payload.target_amount, current_amount=0.0)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return GoalOut.model_validate(goal)


@router.patch("/{goal_id}/contribute", response_model=GoalOut)
def contribute_goal(
    goal_id: int,
    payload: GoalContributeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalOut:
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Цель не найдена")
    _assert_access(db, goal.child_id, user)

    goal.current_amount += payload.amount
    db.commit()
    db.refresh(goal)
    return GoalOut.model_validate(goal)
