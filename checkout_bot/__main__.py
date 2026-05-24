from __future__ import annotations

import asyncio
import sys

from checkout_bot.core.orchestrator import run


def main() -> int:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
