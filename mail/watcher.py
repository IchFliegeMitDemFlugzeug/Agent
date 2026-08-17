"""Отключаемая фоновая проверка разрешённых писем через стандартный IMAP."""

import asyncio
import imaplib
import json
import logging
from typing import Any

from config import IMAP_HOST, IMAP_PASSWORD, IMAP_PORT, IMAP_USER, MAIL_POLL_INTERVAL_SECONDS
from database.db import get_connection, log_event
from mail.filters import is_allowed_sender
from mail.parsers import parse_email

LOGGER = logging.getLogger(__name__)


def _already_processed(message_id: str) -> bool:
    """Проверяет уникальный Message-ID до повторной обработки."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT 1 FROM processed_emails WHERE mailbox='INBOX' AND message_id=?", (message_id,)
        ).fetchone() is not None


def _save_processed(letter: dict[str, Any]) -> None:
    """Атомарно сохраняет факт успешной обработки письма."""
    with get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO processed_emails(mailbox,message_id,sender_address,subject,received_at,payload_json) VALUES('INBOX',?,?,?,?,?)",
            (letter["message_id"], letter["sender"], letter["subject"], letter["received_at"],
             json.dumps({"text": letter["text"]}, ensure_ascii=False)),
        )


def check_mail_once() -> int:
    """Открывает IMAP, обрабатывает новые whitelist-письма и закрывает соединение."""
    processed = 0
    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as client:
        client.login(IMAP_USER, IMAP_PASSWORD)
        status, _ = client.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("IMAP не смог открыть INBOX")
        status, data = client.search(None, "UNSEEN")
        if status != "OK":
            return 0
        for uid in data[0].split():
            try:
                status, fetched = client.fetch(uid, "(RFC822)")
                if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                    continue
                letter = parse_email(fetched[0][1])
                message_id = letter["message_id"] or f"imap-{uid.decode()}"
                letter["message_id"] = message_id
                if not is_allowed_sender(letter["sender"]) or _already_processed(message_id):
                    continue
                _save_processed(letter)
                log_event("email.received", "imap", {"subject": letter["subject"]},
                          external_id=message_id, status="processed")
                processed += 1
            except Exception:
                LOGGER.exception("Ошибка обработки одного письма IMAP")
    return processed


async def run_mail_watcher() -> None:
    """Периодически вызывает блокирующий IMAP-код в отдельном потоке."""
    LOGGER.info("IMAP watcher запущен")
    while True:
        try:
            count = await asyncio.to_thread(check_mail_once)
            if count:
                LOGGER.info("Обработано разрешённых писем: %s", count)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("Ошибка проверки IMAP; следующая попытка будет позже")
        await asyncio.sleep(MAIL_POLL_INTERVAL_SECONDS)
