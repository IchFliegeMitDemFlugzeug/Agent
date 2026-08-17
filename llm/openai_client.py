"""Единственная точка проекта, которая обращается к OpenAI Responses API."""

import asyncio
import logging

from config import OPENAI_API_KEY, OPENAI_MODEL

LOGGER = logging.getLogger(__name__)
NOT_CONFIGURED = "OpenAI API пока не настроен."


def _request(prompt: str) -> str:
    """Выполняет синхронный SDK-вызов внутри рабочего потока."""
    if not OPENAI_API_KEY or not OPENAI_MODEL:
        return NOT_CONFIGURED
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.create(model=OPENAI_MODEL, input=prompt)
        return response.output_text.strip() or "Модель вернула пустой ответ."
    except Exception:
        LOGGER.exception("Ошибка обращения к OpenAI")
        return "Не удалось получить ответ OpenAI. Попробуйте позже."


async def get_text_response(prompt: str) -> str:
    """Не блокирует Telegram event loop во время сетевого запроса."""
    if not prompt.strip():
        return "Сообщение пустое."
    return await asyncio.to_thread(_request, prompt)
