"""Совмещает локальный ``telegram.bot`` с одноимённым пакетом PTB.

Исходный каркас назвал каталог ``telegram``, как и внешняя библиотека. Этот
небольшой совместимый загрузчик сохраняет архитектуру проекта и предоставляет
классы установленного ``python-telegram-bot``.
"""

import sys
from pathlib import Path

_LOCAL_DIR = Path(__file__).resolve().parent
_UPSTREAM_INIT = next(
    (
        Path(entry).resolve() / "telegram" / "__init__.py"
        for entry in sys.path
        if entry and (Path(entry).resolve() / "telegram" / "__init__.py").is_file()
        and (Path(entry).resolve() / "telegram") != _LOCAL_DIR
    ),
    None,
)
if _UPSTREAM_INIT is not None:
    __path__ = [str(_LOCAL_DIR), str(_UPSTREAM_INIT.parent)]
    exec(compile(_UPSTREAM_INIT.read_bytes(), str(_UPSTREAM_INIT), "exec"), globals())
