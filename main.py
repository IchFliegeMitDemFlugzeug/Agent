"""Единая точка запуска Telegram, scheduler и необязательного IMAP watcher."""

import asyncio
import contextlib
import logging

from config import imap_is_configured, validate_config
from core.dispatcher import Dispatcher
from core.scheduler import run_scheduler
from database.db import initialize_database, log_event
from mail.watcher import run_mail_watcher
from telegram.bot import build_application

LOGGER = logging.getLogger(__name__)


async def run() -> None:
    """Запускает компоненты в одном event loop и корректно их останавливает."""
    initialize_database()
    for warning in validate_config(require_telegram=True):
        LOGGER.warning(warning)
    log_event("system.start", "main", status="started")
    application = build_application()
    dispatcher = Dispatcher(application.bot.send_message)
    tasks: list[asyncio.Task[None]] = []
    await application.initialize()
    await application.start()
    if application.updater is None:
        raise RuntimeError("Telegram updater не создан")
    await application.updater.start_polling()
    LOGGER.info("Telegram готов")
    tasks.append(asyncio.create_task(run_scheduler(dispatcher), name="scheduler"))
    if imap_is_configured():
        tasks.append(asyncio.create_task(run_mail_watcher(), name="mail-watcher"))
    else:
        LOGGER.info("IMAP отключён или не настроен")
    try:
        await asyncio.Event().wait()
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        LOGGER.info("Агент остановлен")


def main() -> None:
    """Настраивает безопасный консольный лог и запускает приложение."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    LOGGER.info("Запуск персонального агента")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        LOGGER.info("Получен сигнал остановки")
    except ValueError as exc:
        LOGGER.error("Ошибка конфигурации: %s", exc)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
