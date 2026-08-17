"""Надёжное извлечение основных полей стандартного email-сообщения."""

from email.header import decode_header, make_header
from email.message import Message
from email.policy import default
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import Any

from mail.filters import normalize_address


def _header(value: str | None) -> str:
    """Декодирует MIME-заголовок без падения на пустом значении."""
    return str(make_header(decode_header(value or "")))


def _plain_text(message: Message) -> str:
    """Выбирает обычный текст и пропускает вложения."""
    if message.is_multipart():
        parts = message.walk()
    else:
        parts = (message,)
    chunks: list[str] = []
    for part in parts:
        if part.get_content_type() != "text/plain" or part.get_content_disposition() == "attachment":
            continue
        try:
            chunks.append(part.get_content().strip())
        except (LookupError, UnicodeError):
            payload = part.get_payload(decode=True) or b""
            chunks.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip())
    return "\n".join(chunk for chunk in chunks if chunk)


def parse_email(raw_message: bytes) -> dict[str, Any]:
    """Возвращает безопасный минимальный словарь письма."""
    message = BytesParser(policy=default).parsebytes(raw_message)
    date_value = None
    try:
        if message.get("Date"):
            date_value = parsedate_to_datetime(message["Date"]).isoformat()
    except (TypeError, ValueError):
        date_value = None
    return {
        "message_id": _header(message.get("Message-ID")),
        "sender": normalize_address(_header(message.get("From"))),
        "subject": _header(message.get("Subject")),
        "received_at": date_value,
        "text": _plain_text(message),
    }
