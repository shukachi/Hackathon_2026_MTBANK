from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import COOKIE_NAME, create_access_token, hash_password, verify_password
from app.db import get_db
from app.models.user import Family, RoleEnum, User
from app.schemas.user import LoginRequest, RegisterRequest, UserOut
from app.services import loyalty_service

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_MAX_AGE_SECONDS = 60 * 60  # 1 hour, совпадает с дефолтным JWT_EXPIRE_MIN; cookie просто не должен жить дольше


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # локальная демка; в проде — True (HTTPS)
        max_age=COOKIE_MAX_AGE_SECONDS,
        path="/",
    )


@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> UserOut:
    existing = db.query(User).filter(User.login == payload.login).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Такой логин уже зарегистрирован")

    family = Family(name=f"Семья {payload.full_name}")
    db.add(family)
    db.flush()

    user = User(
        login=payload.login,
        password_hash=hash_password(payload.password),
        role=RoleEnum.parent,
        full_name=payload.full_name,
        family_id=family.id,
    )
    db.add(user)
    db.flush()

    # У родителя свой счёт орешков — баллы копятся раздельно у родителя и ребёнка.
    loyalty_service.get_or_create_account(db, user.id)

    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role.value, user.family_id)
    _set_auth_cookie(response, token)

    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user = db.query(User).filter(User.login == payload.login).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    token = create_access_token(user.id, user.role.value, user.family_id)
    _set_auth_cookie(response, token)

    return UserOut.model_validate(user)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
