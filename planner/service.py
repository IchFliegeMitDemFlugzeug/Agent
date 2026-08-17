"""Минимальный календарь поверх существующей таблицы SQLite."""

import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from config import APP_TIMEZONE
from database.db import get_connection


def _utc_text(value: datetime | str) -> str:
    """Нормализует дату в сортируемый ISO-текст UTC."""
    moment = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo(APP_TIMEZONE))
    return moment.astimezone(timezone.utc).isoformat()


def create_event(title: str, start_at: datetime | str, description: str = "",
                 action: str = "telegram_notify", payload: dict[str, Any] | None = None,
                 timezone_name: str = APP_TIMEZONE, rrule: str | None = None) -> int:
    """Создаёт активное календарное событие и возвращает его id."""
    next_run = _utc_text(start_at)
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO calendar_events(title,description,start_at,timezone,rrule,action,payload_json,next_run_at) VALUES(?,?,?,?,?,?,?,?)",
            (title, description, next_run, timezone_name, rrule, action,
             json.dumps(payload or {}, ensure_ascii=False), next_run),
        )
        return int(cursor.lastrowid)


def get_future_events(limit: int = 20) -> list[dict[str, Any]]:
    """Возвращает активные будущие события в хронологическом порядке."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM calendar_events WHERE enabled=1 AND next_run_at>=? ORDER BY next_run_at LIMIT ?",
            (now, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_nearest_events(limit: int = 5) -> list[dict[str, Any]]:
    """Возвращает несколько ближайших будущих событий."""
    return get_future_events(limit)


def get_due_events(now: datetime | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Находит активные события, время которых уже наступило."""
    boundary = _utc_text(now or datetime.now(timezone.utc))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM calendar_events WHERE enabled=1 AND next_run_at IS NOT NULL AND next_run_at<=? ORDER BY next_run_at LIMIT ?",
            (boundary, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def disable_event(event_id: int) -> bool:
    """Отключает событие и очищает следующее время запуска."""
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE calendar_events SET enabled=0,next_run_at=NULL,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (event_id,),
        )
        return cursor.rowcount > 0


def mark_completed(event_id: int) -> bool:
    """Отмечает одноразовое событие выполненным."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE calendar_events SET enabled=0,last_run_at=?,next_run_at=NULL,updated_at=? WHERE id=?",
            (now, now, event_id),
        )
        return cursor.rowcount > 0
