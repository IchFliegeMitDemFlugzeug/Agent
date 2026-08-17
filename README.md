# Персональный Telegram-агент — MVP

Локальный Python-агент принимает текст и голос в Telegram, выполняет простые
команды без нейросети, хранит сообщения и календарь в SQLite и при необходимости
получает живой ответ через OpenAI. Голос распознаётся **локально** faster-whisper.

## Установка в Windows

Откройте PowerShell в папке проекта и выполните:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Откройте `.env` в Блокноте и укажите:

- `TELEGRAM_BOT_TOKEN` — токен, полученный в Telegram у **@BotFather** командой
  `/newbot` (обязателен);
- `TELEGRAM_ALLOWED_USER_ID` — ваш числовой Telegram ID, чтобы бот отвечал только
  вам (его можно узнать у бота **@userinfobot**);
- `OPENAI_API_KEY` и `OPENAI_MODEL` — нужны только для обычных свободных вопросов;
- `APP_TIMEZONE` — ваш часовой пояс, по умолчанию `Europe/Moscow`;
- настройки Whisper обычно можно оставить как в примере;
- для почты включите `IMAP_ENABLED=1` и заполните `IMAP_HOST`, `IMAP_USER`,
  `IMAP_PASSWORD`. Разрешённые адреса добавляются в таблицу `email_sources`.

Не публикуйте `.env`: в нём находятся ваши секреты.

## Запуск и проверка

```powershell
python main.py
```

Напишите боту `/status`, `/calendar`, затем обычный вопрос и отправьте голосовое.
Команды обрабатываются локально. Для обычного вопроса без ключа бот понятно
сообщит, что OpenAI не настроен. При первом голосовом сообщении faster-whisper
скачает выбранную модель; далее она переиспользуется.

Календарные напоминания с action `telegram_notify` должны иметь в `payload_json`
поля `chat_id` и `text`. Почта по умолчанию отключена, а неизвестные отправители
всегда игнорируются.
