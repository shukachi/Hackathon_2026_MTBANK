from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    title: str
    target_amount: float
    current_amount: float
    created_at: datetime


class GoalCreateRequest(BaseModel):
    child_id: int
    title: str
    target_amount: float


class GoalContributeRequest(BaseModel):
    amount: float
