# Импортируем argparse — стандартный модуль Python для обработки аргументов командной строки.
import argparse

# Импортируем sqlite3 — встроенный в Python драйвер SQLite.
# Никаких дополнительных библиотек для создания базы данных устанавливать не нужно.
import sqlite3

# Импортируем Path — удобный современный интерфейс для работы с путями и папками.
from pathlib import Path


# ---------------------------------------------------------------------------
# СТРУКТУРА КАТАЛОГОВ ПРОЕКТА
# ---------------------------------------------------------------------------

# Здесь перечислены все каталоги, которые должны существовать внутри проекта.
PROJECT_DIRS = [
    # Ядро агента: маршрутизация событий, диспетчеризация, планировщик.
    "core",

    # Работа с Telegram.
    "telegram",

    # Локальное распознавание голосовых сообщений.
    "speech",

    # Работа с электронной почтой.
    "mail",

    # Собственный календарь, напоминания и планирование.
    # Название planner выбрано специально вместо calendar,
    # потому что calendar уже является стандартным модулем Python.
    "planner",

    # Единственная точка взаимодействия с большой языковой моделью.
    "llm",

    # Код работы с SQLite и будущими миграциями БД.
    "database",

    # Постоянные данные программы.
    "data",

    # Временные файлы, например скачанные голосовые сообщения.
    "temp",

    # Текстовые журналы программы, если позже захотим писать их в файлы.
    "logs",
]


# ---------------------------------------------------------------------------
# ШАБЛОННЫЕ ФАЙЛЫ ПРОЕКТА
# ---------------------------------------------------------------------------

# Словарь:
# ключ — относительный путь к файлу;
# значение — первоначальное содержимое файла.
PROJECT_FILES = {
    # -----------------------------------------------------------------------
    # Главная точка запуска программы.
    # -----------------------------------------------------------------------
    "main.py": '''"""
Главная точка запуска персонального агента.

Позже отсюда будут запускаться:
- Telegram-бот;
- внутренний планировщик;
- обработчик почты;
- маршрутизатор событий.
"""

from database.db import get_connection


def main() -> None:
    """Проверяет, что проект и база данных доступны."""

    # Открываем соединение с локальной SQLite-БД.
    connection = get_connection()

    # Выполняем простейший запрос для проверки работоспособности БД.
    connection.execute("SELECT 1")

    # Закрываем соединение после проверки.
    connection.close()

    # Пока просто сообщаем, что каркас проекта успешно работает.
    print("Agent core initialized successfully.")


if __name__ == "__main__":
    # Запускаем main() только при непосредственном запуске этого файла.
    main()
''',

    # -----------------------------------------------------------------------
    # Конфигурация приложения.
    # -----------------------------------------------------------------------
    "config.py": '''"""
Загрузка конфигурации агента из файла .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# Определяем корневую папку проекта.
PROJECT_ROOT = Path(__file__).resolve().parent

# Формируем путь к файлу .env.
ENV_FILE = PROJECT_ROOT / ".env"

# Загружаем переменные окружения из .env.
load_dotenv(ENV_FILE)


# Telegram Bot API token.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# API-ключ OpenAI.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Имя модели вынесено в конфигурацию,
# чтобы её можно было менять без изменения программного кода.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

# Часовой пояс собственного календаря агента.
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "UTC")

# Адрес IMAP-сервера электронной почты.
IMAP_HOST = os.getenv("IMAP_HOST", "")

# Порт защищённого IMAP-соединения.
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

# Логин почтового ящика.
IMAP_USER = os.getenv("IMAP_USER", "")

# Пароль или специальный пароль приложения для почтового ящика.
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")

# Период проверки почты в секундах.
MAIL_POLL_INTERVAL_SECONDS = int(
    os.getenv("MAIL_POLL_INTERVAL_SECONDS", "60")
)

# Период проверки внутренних временных триггеров.
SCHEDULER_POLL_INTERVAL_SECONDS = int(
    os.getenv("SCHEDULER_POLL_INTERVAL_SECONDS", "5")
)
''',

    # -----------------------------------------------------------------------
    # Работа с SQLite.
    # -----------------------------------------------------------------------
    "database/db.py": '''"""
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
''',

    # -----------------------------------------------------------------------
    # Заготовка для будущей системы миграций.
    # -----------------------------------------------------------------------
    "database/migrations.py": '''"""
Здесь позже появится система миграций структуры базы данных.

Миграция — контролируемое изменение структуры уже существующей БД,
например добавление таблицы расходов без удаления старых данных.
"""
''',

    # -----------------------------------------------------------------------
    # Универсальное внутреннее событие агента.
    # -----------------------------------------------------------------------
    "core/events.py": '''"""
Описание внутреннего события агента.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    """Универсальное событие, поступающее во внутреннее ядро агента."""

    # Тип события, например telegram.text или calendar.due.
    type: str

    # Источник события.
    source: str

    # Полезная нагрузка события.
    payload: dict[str, Any] = field(default_factory=dict)
''',

    # -----------------------------------------------------------------------
    # Маршрутизатор.
    # -----------------------------------------------------------------------
    "core/router.py": '''"""
Маршрутизатор событий.

Именно здесь позже будет приниматься решение:

1. Обработать событие обычным Python-кодом.
2. Проигнорировать событие.
3. Передать событие языковой модели.
"""


def route_event(event):
    """Временно возвращает событие без обработки."""

    return event
''',

    # -----------------------------------------------------------------------
    # Диспетчер действий.
    # -----------------------------------------------------------------------
    "core/dispatcher.py": '''"""
Диспетчер действий агента.

Позже здесь будут выполняться действия вроде:

- send_telegram;
- create_calendar_event;
- parse_receipt;
- save_expense;
- invoke_llm.
"""
''',

    # -----------------------------------------------------------------------
    # Фоновый планировщик.
    # -----------------------------------------------------------------------
    "core/scheduler.py": '''"""
Фоновый движок календарных и прочих временных триггеров.

Он будет периодически искать в SQLite события,
у которых наступил next_run_at.
"""
''',

    # -----------------------------------------------------------------------
    # Telegram.
    # -----------------------------------------------------------------------
    "telegram/bot.py": '''"""
Telegram-интерфейс агента.

Здесь позже будут приниматься:
- текстовые сообщения;
- голосовые сообщения;
- команды Telegram.
"""
''',

    # -----------------------------------------------------------------------
    # Локальное распознавание речи.
    # -----------------------------------------------------------------------
    "speech/whisper.py": '''"""
Локальное распознавание голосовых сообщений.

Здесь позже будет подключён faster-whisper.
"""
''',

    # -----------------------------------------------------------------------
    # Почтовый обработчик.
    # -----------------------------------------------------------------------
    "mail/watcher.py": '''"""
Фоновая проверка электронной почты по IMAP.
"""
''',

    # -----------------------------------------------------------------------
    # Фильтры электронной почты.
    # -----------------------------------------------------------------------
    "mail/filters.py": '''"""
Фильтрация почты.

Главный принцип:
обрабатываются только отправители,
явно разрешённые в таблице email_sources.
"""
''',

    # -----------------------------------------------------------------------
    # Парсеры писем.
    # -----------------------------------------------------------------------
    "mail/parsers.py": '''"""
Специализированные парсеры писем.

Позже здесь могут появиться:
- Ozon;
- Wildberries;
- интернет-магазины;
- электронные чеки;
- банки;
- службы доставки.
"""
''',

    # -----------------------------------------------------------------------
    # Собственный календарь.
    # -----------------------------------------------------------------------
    "planner/service.py": '''"""
Сервис собственного календаря агента.

Работает поверх таблицы calendar_events в SQLite.
"""
''',

    # -----------------------------------------------------------------------
    # Клиент языковой модели.
    # -----------------------------------------------------------------------
    "llm/openai_client.py": '''"""
Единственная точка обращения агента к OpenAI API.

Другие части программы не должны напрямую вызывать OpenAI.
"""
''',

    # -----------------------------------------------------------------------
    # requirements.txt.
    # Пока перечисляем библиотеки без жёсткой фиксации версий.
    # -----------------------------------------------------------------------
    "requirements.txt": """python-telegram-bot
faster-whisper
openai
python-dotenv
python-dateutil
""",

    # -----------------------------------------------------------------------
    # Файл переменных окружения.
    # Сюда позже нужно вписать реальные секретные ключи.
    # -----------------------------------------------------------------------
    ".env": """# Telegram Bot API token.
TELEGRAM_BOT_TOKEN=

# OpenAI API key.
OPENAI_API_KEY=

# Имя используемой модели OpenAI.
OPENAI_MODEL=

# Основной часовой пояс собственного календаря.
APP_TIMEZONE=UTC

# Параметры IMAP.
IMAP_HOST=
IMAP_PORT=993
IMAP_USER=
IMAP_PASSWORD=

# Проверять почту раз в 60 секунд.
MAIL_POLL_INTERVAL_SECONDS=60

# Проверять календарные триггеры раз в 5 секунд.
SCHEDULER_POLL_INTERVAL_SECONDS=5
""",

    # -----------------------------------------------------------------------
    # Не допускаем случайную публикацию ключей, БД и временных файлов в Git.
    # -----------------------------------------------------------------------
    ".gitignore": """.env
__pycache__/
*.pyc
*.pyo
*.log
temp/*
logs/*
data/*.db
data/*.db-shm
data/*.db-wal
.venv/
venv/
.idea/
.vscode/
""",

    # -----------------------------------------------------------------------
    # Пустые __init__.py превращают каталоги в нормальные Python-пакеты.
    # -----------------------------------------------------------------------
    "core/__init__.py": "",
    "telegram/__init__.py": "",
    "speech/__init__.py": "",
    "mail/__init__.py": "",
    "planner/__init__.py": "",
    "llm/__init__.py": "",
    "database/__init__.py": "",

    # -----------------------------------------------------------------------
    # .gitkeep позволяет Git сохранить пустые каталоги.
    # -----------------------------------------------------------------------
    "temp/.gitkeep": "",
    "logs/.gitkeep": "",
}


# ---------------------------------------------------------------------------
# SQL-СХЕМА ОСНОВНОЙ БАЗЫ ДАННЫХ
# ---------------------------------------------------------------------------

# Один большой SQL-скрипт создаёт все первоначальные таблицы.
# CREATE TABLE IF NOT EXISTS делает операцию безопасной при повторном запуске.
DATABASE_SCHEMA = """
-- Включаем проверку внешних ключей SQLite.
PRAGMA foreign_keys = ON;

-- Переводим БД в WAL-режим.
-- Он удобнее для приложения, где одновременно работают Telegram,
-- почтовый обработчик и планировщик.
PRAGMA journal_mode = WAL;


-- -------------------------------------------------------------------------
-- СЛУЖЕБНАЯ ИНФОРМАЦИЯ О СХЕМЕ БД
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);


-- -------------------------------------------------------------------------
-- СООБЩЕНИЯ TELEGRAM И ДРУГИЕ ДИАЛОГОВЫЕ СООБЩЕНИЯ
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    source TEXT NOT NULL DEFAULT 'telegram',

    direction TEXT NOT NULL DEFAULT 'in',

    telegram_chat_id INTEGER,

    telegram_message_id INTEGER,

    message_type TEXT NOT NULL DEFAULT 'text',

    text TEXT,

    raw_json TEXT,

    processed INTEGER NOT NULL DEFAULT 0,

    processed_at TEXT
);


-- Индекс нужен для быстрого поиска сообщений конкретного Telegram-чата.
CREATE INDEX IF NOT EXISTS idx_messages_chat
ON messages(telegram_chat_id);


-- Индекс ускоряет поиск ещё не обработанных сообщений.
CREATE INDEX IF NOT EXISTS idx_messages_processed
ON messages(processed);


-- -------------------------------------------------------------------------
-- СОБСТВЕННЫЙ КАЛЕНДАРЬ
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    description TEXT,

    start_at TEXT NOT NULL,

    end_at TEXT,

    timezone TEXT NOT NULL DEFAULT 'UTC',

    rrule TEXT,

    action TEXT NOT NULL DEFAULT 'telegram_notify',

    payload_json TEXT NOT NULL DEFAULT '{}',

    enabled INTEGER NOT NULL DEFAULT 1,

    next_run_at TEXT,

    last_run_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    updated_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);


-- Планировщик в основном будет искать события по next_run_at.
CREATE INDEX IF NOT EXISTS idx_calendar_next_run
ON calendar_events(enabled, next_run_at);


-- -------------------------------------------------------------------------
-- УНИВЕРСАЛЬНЫЕ ТРИГГЕРЫ
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    trigger_type TEXT NOT NULL,

    schedule_json TEXT NOT NULL DEFAULT '{}',

    action TEXT NOT NULL,

    payload_json TEXT NOT NULL DEFAULT '{}',

    enabled INTEGER NOT NULL DEFAULT 1,

    next_run_at TEXT,

    last_run_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    updated_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);


-- Ускоряем выборку активных триггеров, готовых к выполнению.
CREATE INDEX IF NOT EXISTS idx_triggers_next_run
ON triggers(enabled, next_run_at);


-- -------------------------------------------------------------------------
-- БЕЛЫЙ СПИСОК ОТПРАВИТЕЛЕЙ ЭЛЕКТРОННОЙ ПОЧТЫ
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS email_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    address TEXT NOT NULL UNIQUE,

    display_name TEXT,

    source_type TEXT NOT NULL DEFAULT 'generic',

    parser_name TEXT,

    enabled INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);


-- -------------------------------------------------------------------------
-- УЖЕ ОБРАБОТАННЫЕ ПИСЬМА
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS processed_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    mailbox TEXT NOT NULL DEFAULT 'INBOX',

    message_id TEXT NOT NULL,

    sender_address TEXT,

    subject TEXT,

    received_at TEXT,

    processed_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    status TEXT NOT NULL DEFAULT 'processed',

    payload_json TEXT NOT NULL DEFAULT '{}',

    UNIQUE(mailbox, message_id)
);


-- Индекс позволяет быстро находить письма конкретного отправителя.
CREATE INDEX IF NOT EXISTS idx_processed_emails_sender
ON processed_emails(sender_address);


-- -------------------------------------------------------------------------
-- НАСТРОЙКИ АГЕНТА
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,

    value TEXT,

    updated_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);


-- -------------------------------------------------------------------------
-- ОБЩИЙ ЖУРНАЛ СОБЫТИЙ АГЕНТА
-- -------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    level TEXT NOT NULL DEFAULT 'INFO',

    event_type TEXT NOT NULL,

    source TEXT,

    external_id TEXT,

    action TEXT,

    status TEXT,

    message TEXT,

    data_json TEXT NOT NULL DEFAULT '{}'
);


-- Последние события будут регулярно выбираться по времени.
CREATE INDEX IF NOT EXISTS idx_event_log_created_at
ON event_log(created_at);


-- -------------------------------------------------------------------------
-- ПЕРВОНАЧАЛЬНЫЕ СЛУЖЕБНЫЕ ЗНАЧЕНИЯ
-- -------------------------------------------------------------------------

INSERT OR IGNORE INTO schema_meta(key, value)
VALUES ('schema_version', '1');

INSERT OR IGNORE INTO settings(key, value)
VALUES ('scheduler_poll_seconds', '5');

INSERT OR IGNORE INTO settings(key, value)
VALUES ('mail_poll_seconds', '60');

INSERT OR IGNORE INTO settings(key, value)
VALUES ('llm_enabled', '1');
"""


# ---------------------------------------------------------------------------
# ФУНКЦИЯ СОЗДАНИЯ ПАПОК
# ---------------------------------------------------------------------------

def create_directories(project_root: Path) -> None:
    """Создаёт корневую папку проекта и все вложенные каталоги."""

    # Создаём сам корневой каталог.
    # parents=True создаёт при необходимости также родительские каталоги.
    # exist_ok=True запрещает ошибку, если папка уже существует.
    project_root.mkdir(parents=True, exist_ok=True)

    # По очереди перебираем список необходимых каталогов.
    for relative_dir in PROJECT_DIRS:

        # Получаем полный путь конкретного каталога.
        directory = project_root / relative_dir

        # Создаём каталог.
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# ФУНКЦИЯ СОЗДАНИЯ ФАЙЛОВ
# ---------------------------------------------------------------------------

def create_files(project_root: Path, force: bool = False) -> None:
    """
    Создаёт первоначальные файлы проекта.

    force=False:
        существующие файлы не изменяются.

    force=True:
        существующие шаблонные файлы перезаписываются.
    """

    # Перебираем каждый шаблонный файл.
    for relative_path, content in PROJECT_FILES.items():

        # Формируем полный путь к создаваемому файлу.
        file_path = project_root / relative_path

        # На всякий случай создаём родительский каталог файла.
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Если файл уже существует и --force не указан,
        # оставляем пользовательский код нетронутым.
        if file_path.exists() and not force:
            continue

        # Записываем текстовый файл в UTF-8.
        file_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# ФУНКЦИЯ СОЗДАНИЯ SQLITE-БД
# ---------------------------------------------------------------------------

def create_database(project_root: Path) -> Path:
    """
    Создаёт SQLite-БД и гарантирует наличие базовых таблиц.

    Если БД уже существует, данные не удаляются.
    CREATE TABLE IF NOT EXISTS лишь добавляет отсутствующие таблицы.
    """

    # Получаем путь каталога data.
    data_directory = project_root / "data"

    # Гарантируем существование каталога data.
    data_directory.mkdir(parents=True, exist_ok=True)

    # Формируем путь основной базы данных.
    database_path = data_directory / "agent.db"

    # Открываем БД.
    # Если файла ещё нет, sqlite3 автоматически его создаст.
    connection = sqlite3.connect(database_path)

    try:
        # Выполняем сразу весь SQL-скрипт первоначальной схемы.
        connection.executescript(DATABASE_SCHEMA)

        # Явно фиксируем изменения в файле БД.
        connection.commit()

    finally:
        # Закрываем соединение даже в случае возникновения исключения.
        connection.close()

    # Возвращаем путь к созданной или обновлённой базе.
    return database_path


# ---------------------------------------------------------------------------
# ГЛАВНАЯ ФУНКЦИЯ СОЗДАНИЯ ПРОЕКТА
# ---------------------------------------------------------------------------

def create_project(project_root: Path, force: bool = False) -> None:
    """Создаёт каталоги, файлы и SQLite-БД."""

    # Создаём структуру каталогов.
    create_directories(project_root)

    # Создаём первоначальные файлы.
    create_files(project_root, force=force)

    # Создаём БД и сохраняем полученный путь.
    database_path = create_database(project_root)

    # После успешного завершения выводим удобную сводку.
    print()
    print("Проект успешно создан.")
    print(f"Корневая папка: {project_root}")
    print(f"База данных:    {database_path}")
    print()
    print("Следующий шаг:")
    print(f'  cd "{project_root}"')
    print("  python -m venv .venv")
    print()
    print("Затем активировать виртуальное окружение и установить зависимости:")
    print("  pip install -r requirements.txt")
    print()


# ---------------------------------------------------------------------------
# ОБРАБОТКА АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ
# ---------------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    """Разбирает путь проекта и необязательный флаг --force."""

    # Создаём объект парсера командной строки.
    parser = argparse.ArgumentParser(
        description=(
            "Создаёт первоначальную структуру персонального агента "
            "и SQLite-БД."
        )
    )

    # Добавляем необязательный позиционный аргумент target.
    # Если его не указать, программа сама спросит путь.
    parser.add_argument(
        "target",
        nargs="?",
        help="Папка, в которой нужно создать проект.",
    )

    # Добавляем флаг --force.
    # Он нужен только для перезаписи существующих шаблонных файлов.
    parser.add_argument(
        "--force",
        action="store_true",
        help="Перезаписать существующие шаблонные файлы.",
    )

    # Возвращаем разобранные аргументы.
    return parser.parse_args()


# ---------------------------------------------------------------------------
# ТОЧКА ВХОДА УСТАНОВОЧНОГО СКРИПТА
# ---------------------------------------------------------------------------

def main() -> None:
    """Получает путь и запускает создание проекта."""

    # Читаем аргументы командной строки.
    args = parse_arguments()

    # Если путь был передан непосредственно при запуске,
    # используем именно его.
    if args.target:

        # Сохраняем переданную строку.
        target_string = args.target

    else:
        # Если аргумента нет, спрашиваем путь интерактивно.
        target_string = input(
            "Введите полный путь к папке будущего проекта: "
        ).strip()

    # Убираем случайные двойные кавычки вокруг пути.
    # Это удобно при копировании пути из Проводника Windows.
    target_string = target_string.strip('"')

    # Проверяем, что пользователь действительно ввёл путь.
    if not target_string:

        # Останавливаем программу с понятной ошибкой.
        raise SystemExit("Путь к проекту не указан.")

    # Преобразуем строку в объект Path.
    project_root = Path(target_string)

    # Раскрываем символ ~, если он использован.
    project_root = project_root.expanduser()

    # Преобразуем путь в абсолютный.
    project_root = project_root.resolve()

    # Запускаем создание проекта.
    create_project(
        project_root=project_root,
        force=args.force,
    )


# Проверяем, что файл был запущен как самостоятельный скрипт.
if __name__ == "__main__":

    # Запускаем основную функцию.
    main()