from app.models.limit import PeriodEnum
from app.models.transaction import CategoryEnum
from app.services.nl_command_parser import build_preview_text, rule_based_parse


def test_rule_based_parse_sweets_week():
    parsed = rule_based_parse("поставь лимит на сладости 50 рублей в неделю")
    assert parsed.action == "set_limit"
    assert parsed.category == CategoryEnum.sweets
    assert parsed.amount == 50.0
    assert parsed.period == PeriodEnum.week


def test_rule_based_parse_games_month():
    parsed = rule_based_parse("установи лимит 120 на игры в месяц")
    assert parsed.category == CategoryEnum.games
    assert parsed.amount == 120.0
    assert parsed.period == PeriodEnum.month


def test_rule_based_parse_food_default_period():
    parsed = rule_based_parse("ограничь траты на еду до 30 BYN")
    assert parsed.category == CategoryEnum.food
    assert parsed.amount == 30.0
    assert parsed.period == PeriodEnum.week  # default when no period keyword present


def test_rule_based_parse_decimal_amount():
    parsed = rule_based_parse("лимит на подписки 15,5 рублей в месяц")
    assert parsed.category == CategoryEnum.subscriptions
    assert parsed.amount == 15.5
    assert parsed.period == PeriodEnum.month


def test_build_preview_text_contains_amount_and_category():
    parsed = rule_based_parse("лимит на сладости 50 в неделю")
    preview = build_preview_text(parsed)
    assert "50.00" in preview
    assert "sweets" in preview
    assert "неделю" in preview
