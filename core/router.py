"""Маршрутизация: сначала надёжная локальная логика, затем LLM."""

from datetime import datetime
from zoneinfo import ZoneInfo

from config import APP_TIMEZONE
from core.events import Event
from database.db import log_event
from llm.openai_client import get_text_response
from planner.service import get_nearest_events

HELP = "Команды: /status — состояние, /calendar — ближайшие события, /help — помощь. Можно также отправить текст или голосовое."


def _calendar_text() -> str:
    """Форматирует календарь локально, не отправляя данные в LLM."""
    events = get_nearest_events()
    if not events:
        return "Ближайших событий в календаре нет."
    zone = ZoneInfo(APP_TIMEZONE)
    lines = ["Ближайшие события:"]
    for item in events:
        moment = datetime.fromisoformat(item["next_run_at"]).astimezone(zone)
        lines.append(f"• {moment:%d.%m.%Y %H:%M} — {item['title']}")
    return "\n".join(lines)


async def route_event(event: Event) -> str | None:
    """Возвращает готовый ответ либо игнорирует служебное событие."""
    log_event(event.type, event.source, event.payload, external_id=event.external_id)
    if event.type not in {"telegram.text", "telegram.voice_transcribed"}:
        return None
    text = str(event.payload.get("text", "")).strip()
    command = text.split(maxsplit=1)[0].lower() if text else ""
    if command == "/start":
        return "Привет! Я ваш локальный персональный агент. " + HELP
    if command == "/help":
        return HELP
    if command == "/status":
        return "Агент работает. SQLite доступна, локальные команды готовы."
    if command == "/calendar":
        return _calendar_text()
    if not text:
        return "Не удалось получить текст сообщения."
    return await get_text_response(text)
