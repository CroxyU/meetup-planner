"""Конфигурация приложения из переменных окружения."""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""  # обязателен для бота; API стартует и без него
    # polling — локально; webhook — Render (один экземпляр, без Conflict)
    bot_mode: str = "polling"
    webapp_url: str = "http://localhost:5173"
    api_host: str = "0.0.0.0"
    api_port: int = 8000  # на Render подставляется PORT

    @property
    def effective_port(self) -> int:
        return int(os.environ.get("PORT", self.api_port))

    @property
    def effective_bot_mode(self) -> str:
        """На Render всегда webhook (даже если BOT_MODE не задан в Dashboard)."""
        if os.getenv("RENDER", "").lower() in ("true", "1", "yes"):
            return "webhook"
        return (self.bot_mode or "polling").lower().strip()
    database_url: str = "sqlite+aiosqlite:///./meetup.db"
    secret_key: str = "dev-secret-change-in-production"

    # Палитра цветов по умолчанию для выбора при регистрации
    color_palette: list[str] = [
        "#6C9BCF", "#7BC47F", "#E8A87C", "#C38D9E",
        "#85DCB0", "#E27D60", "#41B3A3", "#F4A261",
        "#9B8FD4", "#F28482", "#84A98C", "#52796F",
    ]


settings = Settings()
