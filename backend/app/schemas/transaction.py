from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.transaction import CategoryEnum, TransactionStatusEnum
from app.schemas.card import CardOut


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    amount: float
    category: CategoryEnum
    merchant: str
    status: TransactionStatusEnum
    created_at: datetime


class SimulateTransactionRequest(BaseModel):
    card_id: int
    amount: float
    category: CategoryEnum
    merchant: str


class SimulateTransactionResponse(BaseModel):
    transaction: TransactionOut
    blocked: bool
    reason: str | None = None
    # Сколько орешков начислено кешбэком за эту операцию (0 — если кешбэка нет).
    cashback_points: int = 0
    # Баланс карты ушёл в минус — покупка прошла, но средств не хватило.
    insufficient_funds: bool = False
    # Карта после операции — с актуальным балансом, чтобы фронт обновил реквизиты.
    card: CardOut | None = None
