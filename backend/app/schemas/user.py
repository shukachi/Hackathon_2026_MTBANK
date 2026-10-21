from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.user import RoleEnum

EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
LOGIN_PATTERN = r"^[a-zA-Z0-9_.-]+$"


def _validate_email_value(v: str) -> str:
    v = v.strip()
    if not re.match(EMAIL_PATTERN, v):
        raise ValueError("Неверный формат e-mail")
    return v.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    role: RoleEnum
    full_name: str
    age: int | None
    family_id: int
    parent_id: int | None
    created_at: datetime
    email: str | None = None


class RegisterRequest(BaseModel):
    """Первый шаг регистрации: данные родителя + e-mail для кода верификации."""

    login: str
    password: str
    confirm_password: str
    full_name: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_value(v)

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Логин должен быть от 3 до 32 символов")
        if not re.match(LOGIN_PATTERN, v):
            raise ValueError("Логин может содержать только буквы, цифры, точки, дефисы и подчёркивания")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Укажите имя (минимум 2 символа)")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        return self


class RegisterStartResponse(BaseModel):
    """Ответ первого шага: код отправлен, регистрация ещё не завершена."""

    ok: bool
    email: str
    message: str
    # Демо-режим: код возвращается в ответе, потому что реального SMTP нет.
    # В production это поле убирается.
    demo_code: str | None = None


class RegisterConfirmRequest(BaseModel):
    """Второй шаг: подтверждение кода и завершение регистрации."""

    login: str
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_value(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{6}$", v):
            raise ValueError("Код должен состоять из 6 цифр")
        return v

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        return v.strip()


class ResendCodeRequest(BaseModel):
    """Повторная отправка кода верификации."""

    login: str
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_value(v)

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    login: str
    password: str
