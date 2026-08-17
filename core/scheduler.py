"""Фоновая проверка одноразовых календарных напоминаний."""

import asyncio
import json
import logging

from config import SCHEDULER_POLL_INTERVAL_SECONDS
from core.dispatcher import Dispatcher
from database.db import log_event
from planner.service import get_due_events, mark_completed

LOGGER = logging.getLogger(__name__)


async def run_scheduler(dispatcher: Dispatcher) -> None:
    """Обрабатывает каждое событие отдельно, чтобы ошибка не остановила цикл."""
    LOGGER.info("Scheduler запущен (интервал %s сек.)", SCHEDULER_POLL_INTERVAL_SECONDS)
    while True:
        for event in get_due_events():
            try:
                payload = json.loads(event["payload_json"] or "{}")
                await dispatcher.dispatch(event["action"], payload)
                mark_completed(event["id"])
                log_event("calendar.due", "scheduler", payload, external_id=str(event["id"]),
                          action=event["action"], status="completed")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.exception("Ошибка календарного события id=%s", event["id"])
                log_event("calendar.due", "scheduler", {"error": str(exc)},
                          external_id=str(event["id"]), action=event["action"], status="error")
        await asyncio.sleep(SCHEDULER_POLL_INTERVAL_SECONDS)
