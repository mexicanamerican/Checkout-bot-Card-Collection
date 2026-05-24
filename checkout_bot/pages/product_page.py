from __future__ import annotations

import asyncio

from patchright._impl._errors import TargetClosedError

from checkout_bot.core.exceptions import BrowserClosed, MonitoringFailed
from checkout_bot.pages.base_page import BasePage


class ProductPage(BasePage):
    """Monitor a product page and add it to the cart when stock appears."""

    BUY_BUTTON = (
        'button.single_add_to_cart_button:not([data-product_type="pay_and_collect"])'
    )
    AVAILABLE_LABELS = frozenset({"compra online", "aggiungi al carrello"})
    POPUP_CLOSE = "/html/body/div[2]/div[4]/div/div[2]/div[2]/button"
    POPUP_PROCEED_TO_CART = (
        '//*[@id="page"]/div[4]/footer/div[8]/div/div/div[2]/div/div[2]/div[3]/a'
    )
    MODAL_PROCEED_TO_CART = 'a[href$="/cart/"]:has-text("Vai al carrello")'
    CART_LINK_FALLBACK = 'a[href*="/cart/"][class*="tw-relative"]'
    CART_COUNT_JS = """
        () => {
            const primary = document.querySelector('.tw-bg-primary-dark.tw-text-white span[x-html]');
            if (primary) return parseInt(primary.textContent.trim(), 10) || 0;
            const fallback = document.querySelector('span[x-html^="get"]');
            if (fallback) return parseInt(fallback.textContent.trim(), 10) || 0;
            return 0;
        }
    """

    async def open(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded")
        self.log.info("Product page loaded url=%s", url)
        await self.accept_cookies()
        await self.solve_captcha_if_present()

    async def wait_for_availability(self, poll_interval: float) -> None:
        """Block until the buy button shows an availability label."""
        self.log.info("Waiting for product availability (poll=%.1fs)", poll_interval)
        last_label: str | None = ""
        while True:
            label = await self._read_buy_button_label()
            if label != last_label:
                self.log.info("Buy button label=%r", label)
                last_label = label
            if label in self.AVAILABLE_LABELS:
                self.log.info("Product available (label=%r)", label)
                return
            await asyncio.sleep(poll_interval)

    POST_ADD_TO_CART_DELAY = 3.0

    async def add_to_cart(self) -> None:
        try:
            await self.page.locator(self.BUY_BUTTON).first.click(timeout=2_000)
            self.log.info("Add-to-cart clicked")
        except Exception as e:
            self.log.warning("Add-to-cart click failed; retrying captcha: %s", e)
            await self.solve_captcha_if_present()
            raise MonitoringFailed("add-to-cart click failed") from e

        # A Cloudflare-detection popup occasionally appears here; dismiss it.
        try:
            await self.page.locator(f"xpath={self.POPUP_CLOSE}").click(timeout=5_000)
        except Exception:
            self.log.debug("No popup after add-to-cart")

        await self.solve_captcha_if_present()
        # Give the site time to update the cart badge before we read it.
        await asyncio.sleep(self.POST_ADD_TO_CART_DELAY)

    async def go_to_cart(self) -> None:
        """Navigate from the product page to the cart page."""
        count = await self.page.evaluate(self.CART_COUNT_JS)
        self.log.info("Cart count=%s", count)
        if count <= 0:
            raise MonitoringFailed("product not in cart after add-to-cart")

        try:
            await self.page.locator(f"xpath={self.POPUP_PROCEED_TO_CART}").click(timeout=4_000)
            self.log.info("Proceeded to cart via popup link")
            return
        except Exception:
            self.log.debug("Popup cart link missing; trying add-to-cart modal")

        try:
            await self.page.locator(self.MODAL_PROCEED_TO_CART).first.click(timeout=3_000)
            self.log.info("Proceeded to cart via add-to-cart modal")
            return
        except Exception:
            self.log.debug("Modal cart link missing; using header fallback")

        try:
            await self.page.locator(self.CART_LINK_FALLBACK).click(timeout=10_000)
            self.log.info("Proceeded to cart via header link")
        except Exception as e:
            raise MonitoringFailed("could not navigate to cart") from e

    async def _read_buy_button_label(self) -> str | None:
        js = """
            () => {
                const btn = document.querySelector(
                    'button.single_add_to_cart_button:not([data-product_type="pay_and_collect"])'
                );
                if (!btn) return null;
                const p = btn.querySelector('p[data-add-to-cart-button]');
                return (p ? p.textContent : btn.textContent).trim().toLowerCase();
            }
        """
        try:
            return await self.page.evaluate(js)
        except TargetClosedError as e:
            raise BrowserClosed(e.message) from e
