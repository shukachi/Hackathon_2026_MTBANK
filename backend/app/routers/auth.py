from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import COOKIE_NAME, create_access_token, hash_password, verify_password
from app.db import get_db
from app.models.pending_registration import PendingRegistration
from app.models.user import Family, RoleEnum, User
from app.schemas.user import (
    LoginRequest,
    RegisterConfirmRequest,
    RegisterRequest,
    RegisterStartResponse,
    ResendCodeRequest,
    UserOut,
)
from app.services import email_service, loyalty_service

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_MAX_AGE_SECONDS = 60 * 60  # 1 hour, совпадает с дефолтным JWT_EXPIRE_MIN


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


@router.post("/register/start", response_model=RegisterStartResponse)
def register_start(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterStartResponse:
    """Шаг 1: валидация данных + отправка кода верификации на e-mail.

    Создаётся черновик PendingRegistration (не реальный пользователь).
    Реальный аккаунт создаётся только на шаге 2 (confirm).
    """
    existing = db.query(User).filter(User.login == payload.login).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Такой логин уже зарегистрирован")

    email_exists = db.query(User).filter(User.email == payload.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Этот e-mail уже зарегистрирован")

    # Удаляем старые черновики с тем же логином или e-mail
    db.query(PendingRegistration).filter(
        (PendingRegistration.login == payload.login) | (PendingRegistration.email == payload.email)
    ).delete()
    db.commit()

    code = email_service.send_verification_code(payload.email)

    pending = PendingRegistration(
        login=payload.login,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        email=payload.email,
    )
    db.add(pending)
    db.commit()

    return RegisterStartResponse(
        ok=True,
        email=payload.email,
        message="Код верификации отправлен на указанный e-mail",
        demo_code=code,
    )


@router.post("/register/confirm", response_model=UserOut)
def register_confirm(
    payload: RegisterConfirmRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> UserOut:
    """Шаг 2: проверка кода верификации и завершение регистрации.

    После успешной проверки кода черновик PendingRegistration
    удаляется, создаётся реальный пользователь и семья.
    """
    valid = email_service.verify_code(payload.email, payload.code)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный или просроченный код")

    pending = (
        db.query(PendingRegistration)
        .filter(
            PendingRegistration.login == payload.login,
            PendingRegistration.email == payload.email,
        )
        .first()
    )
    if pending is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Регистрация не найдена или уже завершена")

    # Проверяем, что данные не изменились
    if pending.email != payload.email or pending.login != payload.login:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Данные не соответствуют черновику")

    # Создаём реального пользователя
    family = Family(name=f"Семья {pending.full_name}")
    db.add(family)
    db.flush()

    user = User(
        login=pending.login,
        password_hash=pending.password_hash,
        role=RoleEnum.parent,
        full_name=pending.full_name,
        family_id=family.id,
        email=pending.email,
    )
    db.add(user)
    db.flush()

    loyalty_service.get_or_create_account(db, user.id)

    db.delete(pending)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role.value, user.family_id)
    _set_auth_cookie(response, token)

    return UserOut.model_validate(user)


@router.post("/register/resend")
def register_resend(payload: ResendCodeRequest, db: Session = Depends(get_db)) -> dict:
    """Повторная отправка кода верификации."""
    pending = (
        db.query(PendingRegistration)
        .filter(PendingRegistration.login == payload.login, PendingRegistration.email == payload.email)
        .first()
    )
    if pending is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Регистрация не найдена")

    code = email_service.send_verification_code(pending.email)
    return {"ok": True, "message": "Код отправлен повторно", "demo_code": code}


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