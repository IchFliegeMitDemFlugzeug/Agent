"""
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
