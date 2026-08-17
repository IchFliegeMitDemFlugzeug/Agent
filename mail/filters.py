"""Белый список отправителей электронной почты из SQLite."""

from email.utils import parseaddr

from database.db import get_connection


def normalize_address(value: str) -> str:
    """Извлекает адрес из поля From и приводит его к нижнему регистру."""
    return parseaddr(value)[1].strip().lower()


def is_allowed_sender(value: str) -> bool:
    """Разрешает только явно включённый адрес из email_sources."""
    address = normalize_address(value)
    if not address:
        return False
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM email_sources WHERE lower(address)=? AND enabled=1", (address,)
        ).fetchone()
    return row is not None
