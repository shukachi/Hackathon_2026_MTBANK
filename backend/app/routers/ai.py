"""AI-роуты. Системные промпты держим как константы в коде (TODO: когда появится
папка ai/prompts/ в корне репозитория — читать child_assistant_system.md и
parent_command_system.md оттуда; эта папка сейчас не в зоне backend, поэтому
файлы туда не создаём).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_current_user
from app.db import get_db
from app.models.limit import Limit
from app.models.user import RoleEnum, User
from app.schemas.ai import (
    ChildChatRequest,
    ChildChatResponse,
    ParentCommandApplyRequest,
    ParentCommandRequest,
    ParentCommandResponse,
)
from app.schemas.limit import LimitOut
from app.services import nl_command_parser, ollama_client, rag

router = APIRouter(prefix="/ai", tags=["ai"])

CHILD_ASSISTANT_SYSTEM_PROMPT = (
    "Ты — дружелюбный финансовый помощник для ребёнка/подростка в приложении Moby Family. "
    "Отвечай кратко, просто и по-доброму на русском языке.\n"
    "ВАЖНО: в системном сообщении тебе даны реальные транзакции и готовые суммы по категориям. "
    "Если вопрос про траты — ОБЯЗАТЕЛЬНО назови конкретную сумму в BYN из этих данных "
    "(например: «На игры ты потратил 70.52 BYN за 30 дней»). "
    "Не выдумывай суммы и не отвечай общими словами без чисел. "
    "Если данных по вопросу нет — честно скажи, что таких трат не найдено."
)

DEFAULT_CHILD_REPLY = (
    "Привет! Я могу рассказать, сколько ты потратил на еду, сладости, игрушки, игры, подписки, "
    "образование или развлечения. Спроси, например: 'Сколько я потратил на игры?'"
)


@router.post("/chat", response_model=ChildChatResponse)
def child_chat(
    payload: ChildChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ChildChatResponse:
    if user.role not in (RoleEnum.child, RoleEnum.teen):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступно только ребёнку/подростку")

    context, matched_categories = rag.build_context(db, user.id, payload.message)

    llm_reply = ollama_client.chat(
        CHILD_ASSISTANT_SYSTEM_PROMPT + "\n\n" + context, payload.message
    )
    if llm_reply is not None:
        return ChildChatResponse(reply=llm_reply, source="ollama")

    if matched_categories:
        total = rag.spent_by_categories(db, user.id, matched_categories)
        categories_text = ", ".join(c.value for c in matched_categories)
        reply = (
            f"Похоже, ты спрашиваешь про {categories_text}. "
            f"За последние 30 дней ты потратил на это {total:.2f} BYN."
        )
    else:
        reply = DEFAULT_CHILD_REPLY

    return ChildChatResponse(reply=reply, source="rule_based")


@router.post("/parent-command", response_model=ParentCommandResponse)
def parent_command(
    payload: ParentCommandRequest, db: Session = Depends(get_db), parent: User = Depends(get_current_parent)
) -> ParentCommandResponse:
    child = db.get(User, payload.child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")

    parsed, source = nl_command_parser.parse_parent_command(payload.text)
    preview_text = nl_command_parser.build_preview_text(parsed)

    return ParentCommandResponse(action=parsed.action, parsed=parsed, preview_text=preview_text, source=source)


@router.post("/parent-command/apply", response_model=LimitOut)
def apply_parent_command(
    payload: ParentCommandApplyRequest, db: Session = Depends(get_db), parent: User = Depends(get_current_parent)
) -> LimitOut:
    child = db.get(User, payload.child_id)
    if not child or child.family_id != parent.family_id or child.role == RoleEnum.parent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ребёнок не принадлежит вашей семье")

    limit = (
        db.query(Limit)
        .filter(Limit.child_id == payload.child_id, Limit.category == payload.category)
        .first()
    )
    if limit:
        limit.amount = payload.amount
        limit.period = payload.period
    else:
        limit = Limit(
            child_id=payload.child_id,
            category=payload.category,
            amount=payload.amount,
            period=payload.period,
        )
        db.add(limit)

    db.commit()
    db.refresh(limit)
    return LimitOut.model_validate(limit)
