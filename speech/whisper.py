"""Локальное распознавание речи через одну переиспользуемую Whisper-модель."""

import asyncio
import logging
from pathlib import Path
from threading import Lock
from typing import Any

from config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_LANGUAGE, WHISPER_MODEL

LOGGER = logging.getLogger(__name__)
_model: Any = None
_model_lock = Lock()


def _get_model() -> Any:
    """Лениво загружает модель ровно один раз при первом голосовом сообщении."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from faster_whisper import WhisperModel

                _model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE,
                                      compute_type=WHISPER_COMPUTE_TYPE)
                LOGGER.info("Whisper загружен: model=%s device=%s compute=%s",
                            WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE)
    return _model


def transcribe(audio_path: str | Path) -> str:
    """Распознаёт локальный аудиофайл и возвращает объединённый текст."""
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Аудиофайл не найден: {path}")
    try:
        segments, _ = _get_model().transcribe(str(path), language=WHISPER_LANGUAGE)
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
    except Exception as exc:
        LOGGER.exception("Не удалось распознать голосовое сообщение")
        raise RuntimeError("Не удалось распознать голосовое сообщение.") from exc


async def transcribe_async(audio_path: str | Path) -> str:
    """Выносит тяжёлое CPU-распознавание из Telegram event loop."""
    return await asyncio.to_thread(transcribe, audio_path)
