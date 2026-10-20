"""Парсинг команды родителя на естественном языке в структурированную команду лимита.

Пробуем через LLM (ollama_client.chat), просим вернуть JSON. Если Ollama недоступна
ИЛИ ответ не проходит Pydantic-валидацию — используем rule-based regex fallback.
"""
import json
import re

from pydantic import ValidationError

from app.models.limit import PeriodEnum
from app.models.transaction import CategoryEnum
from app.schemas.ai import ParsedLimitCommand
from app.services import ollama_client

PARENT_COMMAND_SYSTEM_PROMPT = (
    "Ты — помощник банковского приложения Moby Family. Родитель пишет команду на русском "
    "естественном языке про установку лимита трат для ребёнка. Верни СТРОГО JSON без комментариев "
    'в формате {"action": "set_limit", "category": "<одна из food|sweets|toys|games|subscriptions|'
    'education|entertainment|other|null>", "amount": <число>, "period": "week|month"}. '
    "Ничего кроме JSON не пиши."
)

# Ключевые слова категорий (ru) -> значение CategoryEnum. Используется rule-based парсером.
CATEGORY_KEYWORDS: dict[str, CategoryEnum] = {
    "сладост": CategoryEnum.sweets,
    "конфет": CategoryEnum.sweets,
    "шоколад": CategoryEnum.sweets,
    "еда": CategoryEnum.food,
    "еду": CategoryEnum.food,
    "продукт": CategoryEnum.food,
    "игрушк": CategoryEnum.toys,
    "игры": CategoryEnum.games,
    "игра": CategoryEnum.games,
    "игровые": CategoryEnum.games,
    "подпис": CategoryEnum.subscriptions,
    "учеб": CategoryEnum.education,
    "образован": CategoryEnum.education,
    "книг": CategoryEnum.education,
    "развлечен": CategoryEnum.entertainment,
    "кино": CategoryEnum.entertainment,
    "парк": CategoryEnum.entertainment,
}

AMOUNT_RE = re.compile(r"(\d+(?:[.,]\d+)?)")


def rule_based_parse(text: str) -> ParsedLimitCommand:
    lowered = text.lower()

    amount_match = AMOUNT_RE.search(lowered)
    amount = float(amount_match.group(1).replace(",", ".")) if amount_match else 0.0

    category: CategoryEnum | None = None
    for keyword, cat in CATEGORY_KEYWORDS.items():
        if keyword in lowered:
            category = cat
            break

    if "месяц" in lowered:
        period = PeriodEnum.month
    else:
        period = PeriodEnum.week  # по умолчанию, включая явное упоминание "неделю"/"неделя"

    return ParsedLimitCommand(action="set_limit", category=category, amount=amount, period=period)


def _try_llm_parse(text: str) -> ParsedLimitCommand | None:
    raw = ollama_client.chat(PARENT_COMMAND_SYSTEM_PROMPT, text)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return ParsedLimitCommand(**data)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None


def parse_parent_command(text: str) -> tuple[ParsedLimitCommand, str]:
    """Возвращает (parsed, source) где source in {"ollama", "rule_based"}."""
    llm_result = _try_llm_parse(text)
    if llm_result is not None:
        return llm_result, "ollama"
    return rule_based_parse(text), "rule_based"


def build_preview_text(parsed: ParsedLimitCommand) -> str:
    category_text = f"на категорию '{parsed.category.value}'" if parsed.category else "общий (без категории)"
    period_text = "неделю" if parsed.period == PeriodEnum.week else "месяц"
    return f"Будет установлен лимит {parsed.amount:.2f} BYN в {period_text}, {category_text}."
