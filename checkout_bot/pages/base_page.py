from __future__ import annotations

import logging

from patchright.async_api import Page

from checkout_bot.services.captcha_solver import CapSolverClient


class BasePage:
    """Common helpers shared by every page object."""

    COOKIE_ACCEPT_ID = "#onetrust-accept-btn-handler"

    def __init__(
        self,
        page: Page,
        *,
        captcha_solver: CapSolverClient,
        site_key: str,
        logger: logging.Logger | logging.LoggerAdapter,
    ) -> None:
        self.page = page
        self.captcha = captcha_solver
        self.site_key = site_key
        self.log = logger

    async def accept_cookies(self, timeout_ms: int = 5_000) -> None:
        """Dismiss the OneTrust cookie banner if it appears. No-op otherwise."""
        try:
            await self.page.locator(self.COOKIE_ACCEPT_ID).click(timeout=timeout_ms)
            self.log.info("Cookie banner dismissed")
        except Exception:
            self.log.debug("No cookie banner present")

    async def solve_captcha_if_present(self) -> None:
        """Detect Turnstile on the current page and solve it via CapSolver."""
        selector = f'[data-sitekey="{self.site_key}"]'
        if await self.page.locator(selector).count() == 0:
            self.log.debug("No Turnstile captcha on page")
            return
        self.log.info("Turnstile captcha detected; solving")
        await self.captcha.solve_turnstile(self.page, self.page.url, self.site_key)
