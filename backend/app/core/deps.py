"""FastAPI Depends: текущий пользователь, проверка роли родителя, проверка владения ребёнком."""
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import COOKIE_NAME, decode_access_token
from app.db import get_db
from app.models.user import RoleEnum, User


def get_current_user(
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный или просроченный токен")

    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id is not None else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")

    return user


def get_current_parent(user: User = Depends(get_current_user)) -> User:
    if user.role != RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно только родителю")
    return user


def get_child_owned_by_parent(
    child_id: int,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> User:
    child = db.get(User, child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")
    return child
