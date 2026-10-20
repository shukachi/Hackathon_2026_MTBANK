from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.limit import PeriodEnum
from app.models.transaction import CategoryEnum


class LimitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    category: CategoryEnum | None
    amount: float
    period: PeriodEnum
    created_at: datetime
    updated_at: datetime


class LimitUpsertRequest(BaseModel):
    child_id: int
    category: CategoryEnum | None = None
    amount: float
    period: PeriodEnum
