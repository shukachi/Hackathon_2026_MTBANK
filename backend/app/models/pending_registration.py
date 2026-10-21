from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PendingRegistration(Base):
    """Черновик регистрации, ожидающий подтверждения e-mail.

    Создаётся на первом шаге (POST /auth/register/start) и удаляется
    после успешного ввода кода (POST /auth/register/confirm).
    """

    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
