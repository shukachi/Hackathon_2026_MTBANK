from pydantic import BaseModel

from app.schemas.card import CardOut
from app.schemas.user import UserOut


class OnboardingRequest(BaseModel):
    child_full_name: str
    age: int
    consent_given: bool


class OnboardingResponse(BaseModel):
    user: UserOut
    login: str
    temporary_password: str
    card_id: int
    card: CardOut
    message: str = "Сохраните и передайте этот логин и пароль ребёнку. Пароль больше не будет показан."


class FamilyChildOut(BaseModel):
    user: UserOut
    card: CardOut
