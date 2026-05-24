from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from patchright.async_api import Error as PlaywrightError, Page, async_playwright

from checkout_bot.config import AppSettings


_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


@asynccontextmanager
async def launch_page(settings: AppSettings) -> AsyncIterator[Page]:
    """Yield a fresh patchright Page; tears the browser down on exit."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=settings.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=_DEFAULT_USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="it-IT",
            timezone_id="Europe/Rome",
        )
        page = await context.new_page()
        try:
            yield page
        finally:
            for closer in (context.close, browser.close):
                try:
                    await closer()
                except Exception:
                    # Already closed, or driver connection torn down during
                    # shutdown/cancellation. Either way, nothing to do.
                    # NOTE: must not catch BaseException — CancelledError must
                    # propagate so the task can stop on Ctrl+C.
                    pass
