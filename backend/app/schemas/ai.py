from pydantic import BaseModel

from app.models.limit import PeriodEnum
from app.models.transaction import CategoryEnum


class ChildChatRequest(BaseModel):
    message: str


class ChildChatResponse(BaseModel):
    reply: str
    source: str  # "ollama" | "rule_based"


class ParentCommandRequest(BaseModel):
    child_id: int
    text: str


class ParsedLimitCommand(BaseModel):
    action: str = "set_limit"
    category: CategoryEnum | None = None
    amount: float
    period: PeriodEnum = PeriodEnum.week


class ParentCommandResponse(BaseModel):
    action: str
    parsed: ParsedLimitCommand
    preview_text: str
    source: str  # "ollama" | "rule_based"


class ParentCommandApplyRequest(BaseModel):
    child_id: int
    category: CategoryEnum | None = None
    amount: float
    period: PeriodEnum = PeriodEnum.week
