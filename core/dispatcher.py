"""Белый список разрешённых действий агента без eval и исполнения кода."""

from typing import Any, Awaitable, Callable

from llm.openai_client import get_text_response

SendTelegram = Callable[[int, str], Awaitable[None]]


class Dispatcher:
    """Централизованно выполняет только заранее описанные действия."""

    def __init__(self, telegram_sender: SendTelegram) -> None:
        self.telegram_sender = telegram_sender

    async def dispatch(self, action: str, payload: dict[str, Any]) -> str | None:
        """Проверяет action и выполняет соответствующий безопасный обработчик."""
        if action == "telegram_notify":
            chat_id = int(payload["chat_id"])
            text = str(payload.get("text", "Напоминание"))
            # PTB принимает эти параметры как keyword-only, именованный вызов
            # одновременно остаётся удобным для простых тестовых отправителей.
            await self.telegram_sender(chat_id=chat_id, text=text)
            return None
        if action == "llm_response":
            return await get_text_response(str(payload.get("text", "")))
        raise ValueError(f"Неизвестное действие: {action}")
