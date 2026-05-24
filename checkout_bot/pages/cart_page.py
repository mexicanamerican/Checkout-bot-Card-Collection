from __future__ import annotations

from checkout_bot.core.exceptions import MonitoringFailed
from checkout_bot.pages.base_page import BasePage


class CartPage(BasePage):
    """Cart page — single responsibility: click 'proceed to checkout'."""

    PROCEED_TO_CHECKOUT = 'a[href$="/checkout/"]:has-text("Concludi l\'ordine")'
    PROCEED_TO_CHECKOUT_FALLBACK = (
        '//*[@id="content"]/div/div[2]/div[1]/div[2]/div[2]/div[1]/div[1]/div[3]/div[3]/a'
    )

    async def proceed_to_checkout(self, timeout_ms: int = 11_000) -> None:
        try:
            await self.page.locator(self.PROCEED_TO_CHECKOUT).first.click(
                timeout=timeout_ms
            )
            self.log.info("Proceeded to checkout")
        except Exception:
            self.log.debug("Primary checkout link missing; using xpath fallback")
            try:
                await self.page.locator(
                    f"xpath={self.PROCEED_TO_CHECKOUT_FALLBACK}"
                ).click(timeout=timeout_ms)
                self.log.info("Proceeded to checkout via fallback")
            except Exception as e:
                raise MonitoringFailed(
                    "proceed-to-checkout button not clickable"
                ) from e

        await self.accept_cookies()
