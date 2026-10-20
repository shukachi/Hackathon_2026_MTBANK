from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.access_request import AccessRequestStatusEnum


class AccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    feature: str
    status: AccessRequestStatusEnum
    created_at: datetime
    decided_at: datetime | None


class AccessRequestCreateRequest(BaseModel):
    feature: str


class AccessRequestDecideRequest(BaseModel):
    decision: Literal["approved", "denied"]
