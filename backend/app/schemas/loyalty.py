from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoyaltyHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delta: int
    reason: str
    created_at: datetime


class LoyaltyConversionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    points_spent: int
    byn_amount: float
    created_at: datetime


class LoyaltyAccountOut(BaseModel):
    """Счёт орешков пользователя.

    `points` — баланс орешков, `converted_byn` — деньги за конвертированные орешки.
    `points_per_byn` дублирует серверную константу, чтобы фронтенд не хардкодил
    курс конвертации и всегда показывал тот же, что применяет backend.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    points: int
    converted_byn: float
    # Курс конвертации: 1 BYN = N орешков. Не хранится в БД — приходит
    # из серверной константы, чтобы фронт и бэк всегда показывали одно и то же.
    points_per_byn: int = 10
    history: list[LoyaltyHistoryOut] = []
    conversions: list[LoyaltyConversionOut] = []


class ConvertPointsRequest(BaseModel):
    points: int = Field(..., gt=0, description="Сколько орешков конвертировать (кратно 10)")


class ConvertPointsResponse(BaseModel):
    points_spent: int
    byn_amount: float
    points_left: int
    converted_byn: float
    account: LoyaltyAccountOut
