"""Безопасная загрузка настроек приложения из ``.env``."""

import os
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def _integer(name: str, default: int) -> int:
    """Читает целое число и выдаёт понятную ошибку конфигурации."""
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} должен быть целым числом") from exc


def _enabled(name: str, default: bool = False) -> bool:
    """Преобразует распространённые значения переменной в bool."""
    return os.getenv(name, "1" if default else "0").strip().lower() in {
        "1", "true", "yes", "on",
    }


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ALLOWED_USER_ID = _integer("TELEGRAM_ALLOWED_USER_ID", 0) or None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "").strip()
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Moscow").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small").strip()
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu").strip()
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8").strip()
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru").strip()
IMAP_ENABLED = _enabled("IMAP_ENABLED")
IMAP_HOST = os.getenv("IMAP_HOST", "").strip()
IMAP_PORT = _integer("IMAP_PORT", 993)
IMAP_USER = os.getenv("IMAP_USER", "").strip()
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
MAIL_POLL_INTERVAL_SECONDS = max(1, _integer("MAIL_POLL_INTERVAL_SECONDS", 60))
SCHEDULER_POLL_INTERVAL_SECONDS = max(
    1, _integer("SCHEDULER_POLL_INTERVAL_SECONDS", 5)
)


def validate_config(require_telegram: bool = True) -> list[str]:
    """Проверяет настройки; необязательные интеграции возвращает предупреждениями."""
    if require_telegram and not TELEGRAM_BOT_TOKEN:
        raise ValueError("Не заполнен TELEGRAM_BOT_TOKEN в файле .env")
    try:
        ZoneInfo(APP_TIMEZONE)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Неизвестный APP_TIMEZONE: {APP_TIMEZONE}") from exc
    warnings: list[str] = []
    if not OPENAI_API_KEY:
        warnings.append("OpenAI отключён: OPENAI_API_KEY не задан")
    if IMAP_ENABLED and not all((IMAP_HOST, IMAP_USER, IMAP_PASSWORD)):
        warnings.append("IMAP отключён: параметры подключения заполнены не полностью")
    return warnings


def imap_is_configured() -> bool:
    """Сообщает, можно ли безопасно запускать почтовый watcher."""
    return IMAP_ENABLED and bool(IMAP_HOST and IMAP_USER and IMAP_PASSWORD)
