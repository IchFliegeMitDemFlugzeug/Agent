"""
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
