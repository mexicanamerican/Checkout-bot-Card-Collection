from __future__ import annotations

import logging
import subprocess
import sys
from contextlib import contextmanager
from typing import Iterator


_log = logging.getLogger(__name__)


@contextmanager
def prevent_system_sleep() -> Iterator[None]:
    """Keep the host awake for the duration of the block (macOS + Windows)."""
    process = _start()
    try:
        yield
    finally:
        if process is not None:
            process.terminate()
            _log.info("Sleep-prevention process terminated")


def _start() -> subprocess.Popen[bytes] | None:
    if sys.platform == "darwin":
        return subprocess.Popen(
            ["caffeinate", "-d", "-i"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if sys.platform == "win32":
        cmd = [
            sys.executable, "-c",
            "import ctypes, time\n"
            "while True:\n"
            "    ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0)\n"
            "    time.sleep(0.1)\n"
            "    ctypes.windll.user32.mouse_event(0x0001, 0, 0, 0, 0)\n"
            "    time.sleep(59)\n",
        ]
        startupinfo = None
        if hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
        )
    _log.warning("Sleep prevention not implemented for %s", sys.platform)
    return None
