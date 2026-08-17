"""
Базовые функции работы с SQLite.
"""

import sqlite3
from pathlib import Path


# Получаем корневую папку проекта.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Формируем абсолютный путь к основной базе данных.
DATABASE_PATH = PROJECT_ROOT / "data" / "agent.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает соединение с основной SQLite-БД."""

    # Открываем SQLite-БД.
    connection = sqlite3.connect(DATABASE_PATH)

    # Позволяем получать строки результата по именам столбцов.
    connection.row_factory = sqlite3.Row

    # Включаем поддержку внешних ключей для данного соединения.
    connection.execute("PRAGMA foreign_keys = ON")

    # Возвращаем готовое соединение вызывающему коду.
    return connection
