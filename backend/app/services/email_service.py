import random
import time
from typing import Optional

# В памяти хранилище кодов (в продакшене — Redis или БД)
_verification_codes: dict[str, dict] = {}

CODE_EXPIRY_SECONDS = 600  # 10 минут


def generate_verification_code() -> str:
    """Генерирует 6-значный код верификации"""
    return str(random.randint(100000, 999999))


def send_verification_code(email: str) -> str:
    """Отправляет код верификации на e-mail.

    В демо-режиме код возвращается в ответе (в консоль тоже логируется).
    В production здесь нужно интегрироваться с Email-провайдером
    (SendGrid, AWS SES, SMTP и т.д.).
    """
    code = generate_verification_code()
    _verification_codes[email] = {
        "code": code,
        "created_at": time.time(),
        "attempts": 0,
    }
    print(f"[EMAIL SERVICE] Код {code} отправлен на {email}")
    return code


def verify_code(email: str, code: str) -> bool:
    """Проверяет код верификации. Возвращает True только при совпадении."""
    if email not in _verification_codes:
        return False

    entry = _verification_codes[email]

    # Проверяем срок действия кода (10 минут)
    if time.time() - entry["created_at"] > CODE_EXPIRY_SECONDS:
        del _verification_codes[email]
        return False

    # Проверяем количество попыток (максимум 5 попыток)
    if entry["attempts"] >= 5:
        del _verification_codes[email]
        return False

    entry["attempts"] += 1

    if entry["code"] == code:
        del _verification_codes[email]
        return True

    return False


def resend_verification_code(email: str) -> str:
    """Отправляет повторный код верификации"""
    return send_verification_code(email)