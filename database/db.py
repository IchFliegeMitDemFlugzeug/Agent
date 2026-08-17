"""Небольшой синхронный слой доступа к существующей SQLite-БД."""

import json
import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "agent.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 source TEXT NOT NULL DEFAULT 'telegram', direction TEXT NOT NULL DEFAULT 'in',
 telegram_chat_id INTEGER, telegram_message_id INTEGER, message_type TEXT NOT NULL DEFAULT 'text',
 text TEXT, raw_json TEXT, processed INTEGER NOT NULL DEFAULT 0, processed_at TEXT);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(telegram_chat_id);
CREATE TABLE IF NOT EXISTS calendar_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, start_at TEXT NOT NULL,
 end_at TEXT, timezone TEXT NOT NULL DEFAULT 'UTC', rrule TEXT, action TEXT NOT NULL DEFAULT 'telegram_notify',
 payload_json TEXT NOT NULL DEFAULT '{}', enabled INTEGER NOT NULL DEFAULT 1, next_run_at TEXT, last_run_at TEXT,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
CREATE INDEX IF NOT EXISTS idx_calendar_next_run ON calendar_events(enabled,next_run_at);
CREATE TABLE IF NOT EXISTS email_sources (
 id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT NOT NULL UNIQUE, display_name TEXT,
 source_type TEXT NOT NULL DEFAULT 'generic', parser_name TEXT, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
CREATE TABLE IF NOT EXISTS processed_emails (
 id INTEGER PRIMARY KEY AUTOINCREMENT, mailbox TEXT NOT NULL DEFAULT 'INBOX', message_id TEXT NOT NULL,
 sender_address TEXT, subject TEXT, received_at TEXT,
 processed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 status TEXT NOT NULL DEFAULT 'processed', payload_json TEXT NOT NULL DEFAULT '{}', UNIQUE(mailbox,message_id));
CREATE TABLE IF NOT EXISTS settings (
 key TEXT PRIMARY KEY, value TEXT, updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
CREATE TABLE IF NOT EXISTS event_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 level TEXT NOT NULL DEFAULT 'INFO', event_type TEXT NOT NULL, source TEXT, external_id TEXT,
 action TEXT, status TEXT, message TEXT, data_json TEXT NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS idx_event_log_created_at ON event_log(created_at);
INSERT OR IGNORE INTO schema_meta(key,value) VALUES ('schema_version','1');
"""


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с foreign keys, WAL и ожиданием занятой БД."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_database() -> None:
    """Без удаления данных добавляет отсутствующие таблицы и индексы."""
    with get_connection() as connection:
        connection.executescript(SCHEMA)


def save_message(direction: str, text: str, chat_id: int | None = None,
                 message_id: int | None = None, message_type: str = "text",
                 source: str = "telegram", raw: dict[str, Any] | None = None) -> int:
    """Сохраняет входящее сообщение или ответ агента."""
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO messages(source,direction,telegram_chat_id,telegram_message_id,message_type,text,raw_json) VALUES(?,?,?,?,?,?,?)",
            (source, direction, chat_id, message_id, message_type, text,
             json.dumps(raw, ensure_ascii=False) if raw is not None else None),
        )
        return int(cursor.lastrowid)


def save_incoming_message(text: str, **kwargs: Any) -> int:
    """Удобная обёртка для входящего сообщения."""
    return save_message("in", text, **kwargs)


def save_agent_response(text: str, **kwargs: Any) -> int:
    """Удобная обёртка для исходящего ответа."""
    return save_message("out", text, **kwargs)


def log_event(event_type: str, source: str | None = None,
              data: dict[str, Any] | None = None, **fields: Any) -> int:
    """Записывает структурированное внутреннее событие."""
    allowed = {key: fields.get(key) for key in ("level", "external_id", "action", "status", "message")}
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO event_log(level,event_type,source,external_id,action,status,message,data_json) VALUES(?,?,?,?,?,?,?,?)",
            (allowed["level"] or "INFO", event_type, source, allowed["external_id"],
             allowed["action"], allowed["status"], allowed["message"],
             json.dumps(data or {}, ensure_ascii=False, default=str)),
        )
        return int(cursor.lastrowid)


def get_setting(key: str, default: str | None = None) -> str | None:
    """Читает настройку либо возвращает default."""
    with get_connection() as connection:
        row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str | None) -> None:
    """Создаёт или атомарно обновляет настройку."""
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')",
            (key, value),
        )
