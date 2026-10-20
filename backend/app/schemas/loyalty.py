from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoyaltyHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delta: int
    reason: str
    created_at: datetime


class LoyaltyAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    points: int
    history: list[LoyaltyHistoryOut] = []
