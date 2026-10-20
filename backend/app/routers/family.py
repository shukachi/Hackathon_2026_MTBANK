import secrets
import string
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent
from app.core.security import hash_password
from app.db import get_db
from app.models.card import Card, CardDesignEnum, CardStatusEnum
from app.models.user import RoleEnum, User
from app.schemas.card import CardOut
from app.schemas.family import FamilyChildOut, OnboardingRequest, OnboardingResponse
from app.schemas.user import UserOut
from app.services import loyalty_service

router = APIRouter(prefix="/family", tags=["family"])

CHILD_AGE_MIN, CHILD_AGE_MAX = 7, 13
TEEN_AGE_MIN, TEEN_AGE_MAX = 14, 17


def _transliterate(text: str) -> str:
    """Грубая транслитерация кириллицы в латиницу для генерации логина."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
        "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    normalized = unicodedata.normalize("NFKC", text.lower())
    return "".join(table.get(ch, ch if ch.isalnum() else "") for ch in normalized)


def _generate_unique_login(db: Session, full_name: str, age: int) -> str:
    first_name = full_name.strip().split(" ")[0] if full_name.strip() else "child"
    base = _transliterate(first_name) or "child"
    candidate = f"{base}{age}"
    suffix = 1
    while db.query(User).filter(User.login == candidate).first() is not None:
        suffix += 1
        candidate = f"{base}{age}_{suffix}"
    return candidate


def _generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(10))


def _generate_masked_number() -> str:
    last4 = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"**** **** **** {last4}"


@router.post("/onboarding", response_model=OnboardingResponse)
def onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> OnboardingResponse:
    if not payload.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо согласие законного представителя (consent_given=true)",
        )

    if CHILD_AGE_MIN <= payload.age <= CHILD_AGE_MAX:
        role = RoleEnum.child
        design = CardDesignEnum.child
    elif TEEN_AGE_MIN <= payload.age <= TEEN_AGE_MAX:
        role = RoleEnum.teen
        design = CardDesignEnum.teen
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Возраст должен быть от {CHILD_AGE_MIN} до {TEEN_AGE_MAX} лет",
        )

    login = _generate_unique_login(db, payload.child_full_name, payload.age)
    temp_password = _generate_temp_password()

    child = User(
        login=login,
        password_hash=hash_password(temp_password),
        role=role,
        full_name=payload.child_full_name,
        age=payload.age,
        family_id=parent.family_id,
        parent_id=parent.id,
    )
    db.add(child)
    db.flush()

    card = Card(
        user_id=child.id,
        masked_number=_generate_masked_number(),
        status=CardStatusEnum.active,
        design=design,
        balance=payload.initial_balance,
    )
    db.add(card)

    loyalty_service.get_or_create_account(db, child.id)

    db.commit()
    db.refresh(child)
    db.refresh(card)

    return OnboardingResponse(
        user=UserOut.model_validate(child),
        login=login,
        temporary_password=temp_password,
        card_id=card.id,
        card=CardOut.model_validate(card),
    )


@router.get("/children", response_model=list[FamilyChildOut])
def list_children(
    db: Session = Depends(get_db),
    parent: User = Depends(get_current_parent),
) -> list[FamilyChildOut]:
    """Все дети текущего родителя вместе с их картами — чтобы фронтенд мог
    восстановить список семьи после перезагрузки страницы без localStorage-кэша.

    У ребёнка может быть несколько карт: в `cards` — все они, в `card` —
    основная (первая выпущенная), для обратной совместимости с фронтом."""
    children = (
        db.query(User)
        .filter(User.family_id == parent.family_id, User.parent_id == parent.id)
        .all()
    )
    result: list[FamilyChildOut] = []
    for child in children:
        cards = (
            db.query(Card)
            .filter(Card.user_id == child.id)
            .order_by(Card.created_at.asc())
            .all()
        )
        if not cards:
            continue
        result.append(
            FamilyChildOut(
                user=UserOut.model_validate(child),
                card=CardOut.model_validate(cards[0]),
                cards=[CardOut.model_validate(c) for c in cards],
            )
        )
    return result
