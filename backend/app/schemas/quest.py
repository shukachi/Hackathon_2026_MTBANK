from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.quest import QuestStatusEnum


class QuestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    title: str
    description: str
    reward_points: int
    status: QuestStatusEnum
    created_by: int
    created_at: datetime
    completed_at: datetime | None


class QuestCreateRequest(BaseModel):
    child_id: int
    title: str
    description: str = ""
    reward_points: int = 0
