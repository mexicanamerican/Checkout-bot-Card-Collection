from __future__ import annotations

import logging
from typing import Any, MutableMapping


_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger once. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _CONFIGURED = True


class _ContextAdapter(logging.LoggerAdapter):
    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        if self.extra:
            ctx = " ".join(f"{k}={v}" for k, v in self.extra.items())
            return f"[{ctx}] {msg}", kwargs
        return msg, kwargs


def get_logger(name: str, **context: Any) -> _ContextAdapter:
    """Return a logger that prepends context (e.g. task_id=3) to every record."""
    return _ContextAdapter(logging.getLogger(name), context)
