from pydantic import BaseModel

from app.schemas.card import CardOut
from app.schemas.user import UserOut


class OnboardingRequest(BaseModel):
    child_full_name: str
    age: int
    consent_given: bool
    initial_balance: float = 0.0


class OnboardingResponse(BaseModel):
    user: UserOut
    login: str
    temporary_password: str
    card_id: int
    card: CardOut
    message: str = "Сохраните и передайте этот логин и пароль ребёнку. Пароль больше не будет показан."


class FamilyChildOut(BaseModel):
    user: UserOut
    # Основная (первая выпущенная) карта — для совместимости с текущим фронтом.
    card: CardOut
    # Все карты ребёнка — у ребёнка их может быть несколько.
    cards: list[CardOut] = []
