"""Импортируем все модели сюда, чтобы Base.metadata видела все таблицы при create_all."""
from app.models.access_request import AccessRequest, AccessRequestStatusEnum  # noqa: F401
from app.models.card import Card, CardDesignEnum, CardStatusEnum  # noqa: F401
from app.models.goal import Goal  # noqa: F401
from app.models.limit import Limit, PeriodEnum  # noqa: F401
from app.models.loyalty import LoyaltyAccount, LoyaltyConversion, LoyaltyHistory  # noqa: F401
from app.models.qr_payment import QrPayment, QrPaymentStatusEnum  # noqa: F401
from app.models.quest import Quest, QuestStatusEnum  # noqa: F401
from app.models.transaction import CategoryEnum, Transaction, TransactionStatusEnum  # noqa: F401
from app.models.user import Family, RoleEnum, User  # noqa: F401
