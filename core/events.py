"""Простые объекты внутренних событий без сложной event-bus системы."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Event:
    """Описывает одно событие, поступившее в ядро агента."""

    type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    external_id: str | None = None

    def __post_init__(self) -> None:
        """Не допускает событий без обязательных идентификаторов."""
        if not self.type.strip() or not self.source.strip():
            raise ValueError("У события должны быть type и source")
