"""Проверка подписи Telegram Web App initData."""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException

from app.config import settings


def validate_telegram_init_data(init_data: str) -> dict:
    """Возвращает распарсенные данные пользователя или 401."""
    if not init_data:
        raise HTTPException(status_code=401, detail="initData отсутствует")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="hash отсутствует")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=401, detail="Неверная подпись initData")

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="user отсутствует в initData")

    return json.loads(unquote(user_raw))
