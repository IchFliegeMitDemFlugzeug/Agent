"""Telegram text/voice интерфейс на python-telegram-bot."""

import logging
import tempfile
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT, TELEGRAM_ALLOWED_USER_ID, TELEGRAM_BOT_TOKEN
from core.events import Event
from core.router import route_event
from database.db import save_agent_response, save_incoming_message
from speech.whisper import transcribe_async

LOGGER = logging.getLogger(__name__)
TEMP_DIR = PROJECT_ROOT / "temp"


def _allowed(update: Any) -> bool:
    """Игнорирует чужого пользователя, если владелец задан в .env."""
    user = update.effective_user
    return bool(user) and (TELEGRAM_ALLOWED_USER_ID is None or user.id == TELEGRAM_ALLOWED_USER_ID)


async def _process(update: Any, text: str, event_type: str, message_type: str) -> None:
    """Единый путь текста и уже распознанного голоса через Router."""
    if not _allowed(update) or not update.effective_message or not update.effective_chat:
        return
    message = update.effective_message
    save_incoming_message(text, chat_id=update.effective_chat.id, message_id=message.message_id,
                          message_type=message_type)
    response = await route_event(Event(event_type, "telegram", {"text": text, "chat_id": update.effective_chat.id},
                                       external_id=str(message.message_id)))
    if response:
        await message.reply_text(response)
        save_agent_response(response, chat_id=update.effective_chat.id, message_type="text")


async def handle_text(update: Any, context: Any) -> None:
    """Обрабатывает команды и обычный текст, не давая ошибке остановить бота."""
    if not _allowed(update):
        return
    try:
        await _process(update, update.effective_message.text or "", "telegram.text", "text")
    except Exception:
        LOGGER.exception("Ошибка обработки Telegram-текста")
        await update.effective_message.reply_text("Не удалось обработать сообщение.")


async def handle_voice(update: Any, context: Any) -> None:
    """Скачивает voice, локально распознаёт и гарантированно удаляет временный файл."""
    if not _allowed(update):
        return
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    path: Path | None = None
    try:
        voice = update.effective_message.voice
        telegram_file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(dir=TEMP_DIR, suffix=".ogg", delete=False) as temporary:
            path = Path(temporary.name)
        await telegram_file.download_to_drive(custom_path=path)
        text = await transcribe_async(path)
        await _process(update, text, "telegram.voice_transcribed", "voice")
    except Exception:
        LOGGER.exception("Ошибка обработки Telegram voice")
        await update.effective_message.reply_text("Не удалось распознать голосовое сообщение.")
    finally:
        if path:
            path.unlink(missing_ok=True)


def build_application() -> Any:
    """Собирает PTB Application и регистрирует обработчики."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Не заполнен TELEGRAM_BOT_TOKEN в файле .env")
    from telegram.ext import Application, MessageHandler, filters

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    return application
