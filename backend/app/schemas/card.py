from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.card import CardDesignEnum, CardStatusEnum


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    masked_number: str
    status: CardStatusEnum
    design: CardDesignEnum
    created_at: datetime
