from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.transaction import CategoryEnum


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite отдаёт datetime без tzinfo.

    Без нормализации браузер прочитает «2026-10-21T12:00:00» как местное время
    и посчитает обратный отсчёт неправильно. Поэтому на выход всегда UTC с
    явным маркером +00:00.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class QrPaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    user_id: int
    card_id: int
    category: CategoryEnum
    amount: float | None
    status: str
    merchant: str
    created_at: datetime
    expires_at: datetime
    paid_at: datetime | None

    @field_serializer("created_at", "expires_at", "paid_at")
    def _serialize_datetime(self, value: datetime | None) -> datetime | None:
        return _as_utc(value)


class CreateQrRequest(BaseModel):
    category: CategoryEnum
    card_id: int
    # Сумма не обязательна (её может прислать терминал), но если указана —
    # должна быть больше нуля. `gt=0` срабатывает только на заданном значении,
    # `None` остаётся допустимым.
    amount: float | None = Field(default=None, gt=0)
    ttl_minutes: int = Field(default=10, ge=1, le=120)


class CreateQrResponse(BaseModel):
    token: str
    expires_at: datetime
    # Готовая ссылка/строка для кодирования в QR.
    payload: str
    ttl_minutes: int

    @field_serializer("expires_at")
    def _serialize_datetime(self, value: datetime) -> datetime:
        return _as_utc(value)


class PayQrRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    merchant: str | None = None


class PayQrResponse(BaseModel):
    qr_payment: QrPaymentOut
    transaction_id: int
    debited_amount: float
    card_balance_left: float
