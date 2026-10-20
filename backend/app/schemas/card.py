from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.card import CardDesignEnum, CardStatusEnum


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    masked_number: str
    status: CardStatusEnum
    design: CardDesignEnum
    balance: float
    created_at: datetime


class IssueCardRequest(BaseModel):
    """Выпуск дополнительной карты ребёнку от родителя."""

    child_id: int
    design: CardDesignEnum | None = Field(
        default=None,
        description="Дизайн карты. Если не задан — берётся по возрасту ребёнка.",
    )
    balance: float = Field(
        default=0.0,
        ge=0,
        description="Стартовый баланс карты, BYN. Родитель заводит карманные деньги ребёнку.",
    )


class TopUpCardRequest(BaseModel):
    """Пополнение баланса карты (перевод от родителя)."""

    amount: float = Field(..., gt=0, description="Сумма пополнения, BYN")
