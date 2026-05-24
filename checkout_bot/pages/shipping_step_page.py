from __future__ import annotations

from checkout_bot.core.exceptions import FormFillFailed
from checkout_bot.pages.base_page import BasePage


class ShippingStepPage(BasePage):
    """First step on the new ToysCenter checkout: pick a shipping rate."""

    HOME_DELIVERY_RADIO = (
        'input[name="stepForm.selected_shipping_rate"]'
        '[aria-label="Consegna a domicilio"]'
    )
    ANY_SHIPPING_RADIO = 'input[name="stepForm.selected_shipping_rate"]'
    # Multiple steps render a "Continua" button; only the active step's button is visible.
    CONTINUE_BUTTON = 'button:visible:has-text("Continua")'

    async def select_and_continue(self) -> None:
        try:
            await self._select_home_delivery()
            await self.page.locator(self.CONTINUE_BUTTON).first.click(timeout=10_000)
            self.log.info("Shipping step submitted")
        except Exception as e:
            raise FormFillFailed(f"shipping step failed: {e}") from e

    async def _select_home_delivery(self) -> None:
        try:
            await self.page.locator(self.HOME_DELIVERY_RADIO).check(timeout=5_000)
            self.log.info("Selected 'Consegna a domicilio'")
            return
        except Exception:
            self.log.debug("Home-delivery radio missing; selecting first available rate")

        await self.page.locator(self.ANY_SHIPPING_RADIO).first.check(timeout=5_000)
        self.log.info("Selected first available shipping rate")
