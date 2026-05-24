from __future__ import annotations

import json
import time

from patchright.async_api import FrameLocator

from checkout_bot.config import TaskRow
from checkout_bot.core.exceptions import PaymentFailed
from checkout_bot.pages.base_page import BasePage


# Adyen Secure Fields wrap each iframe in a <span data-cse="..."> that uses
# the SDK's stable internal field names — locale-independent and version-safe.
_CARD_NUMBER_CSE = "encryptedCardNumber"
_EXPIRY_CSE = "encryptedExpiryDate"
_CVV_CSE = "encryptedSecurityCode"

# Delay between keystrokes (ms). Adyen Secure Fields reject bursts that look
# robotic; a small per-key delay keeps the input plausibly human.
_KEYSTROKE_DELAY_MS = 60


class PaymentPage(BasePage):
    """Adyen credit-card payment + confirmation handling."""

    CC_RADIO = "#payment_method_adyen"
    PAYMENT_MOUNT = "#wc_adyen_payment_mount_node"
    HOLDER_NAME = "input[name='holderName']"
    # Hidden input Adyen keeps in sync with its component state. Reading
    # `isValid` here is how we know the iframes accepted real input.
    PAYMENT_STATE = "#wc_adyen_payment_data"
    FIRST_IFRAME = 'span[data-cse="encryptedCardNumber"] iframe'
    PLACE_ORDER = "#place_order"
    RETRY_PAYMENT = "//a[contains(text(), 'Ritenta il pagamento')]"
    CONFIRMATION_TEXT = "Grazie per il tuo ordine"

    async def pay(self, task: TaskRow, confirmation_timeout_seconds: int) -> None:
        await self._select_credit_card()
        # Fill top-to-bottom to avoid bouncing the viewport: card → expiry →
        # CVV iframes, then the (lower) holder-name field.
        time.sleep(5)
        await self._fill_card_iframes(
            card_number=task.numero_carta,
            expiry=task.scadenza_carta,
            cvv=task.cvv,
        )
        await self._fill_cardholder_name(task.titolare_carta)
        await self._submit()
        await self._await_confirmation(confirmation_timeout_seconds)

    async def _select_credit_card(self) -> None:
        await self.page.locator(self.CC_RADIO).click(timeout=5_000)
        self.log.info("Credit-card payment method selected")
        mount = self.page.locator(self.PAYMENT_MOUNT)
        await mount.wait_for(state="visible", timeout=10_000)
        # Park the mount at the top of the viewport so the card iframes,
        # holder field, and place-order button all fit below it without
        # further per-field scrolling.
        await mount.evaluate("el => el.scrollIntoView({block: 'start'})")
        # Wait until Adyen has actually bootstrapped the secured-fields
        # iframe, not just rendered the mount container with its spinner.
        await self.page.locator(self.FIRST_IFRAME).wait_for(
            state="attached", timeout=15_000
        )

    async def _fill_cardholder_name(self, name: str) -> None:
        # Holder name is a regular input outside any iframe — fill() is the
        # straightforward way and only scrolls if it isn't already on screen
        # (it usually is, after the mount was parked at viewport top).
        try:
            await self.page.locator(self.HOLDER_NAME).fill(name)
            self.log.info("Cardholder name filled")
        except Exception as e:
            self.log.warning("Cardholder name fill failed: %s", e)

    async def _fill_card_iframes(self, *, card_number: str, expiry: str, cvv: str) -> None:
        await self._fill_iframe(_CARD_NUMBER_CSE, card_number, "card number")
        await self._fill_iframe(_EXPIRY_CSE, expiry, "expiry")
        await self._fill_iframe(_CVV_CSE, cvv, "cvv")

    async def _fill_iframe(self, cse_field: str, value: str, label: str) -> None:
        # Adyen Secure Field iframes are cross-origin. Locator.click() on the
        # input inside the FrameLocator goes through Patchright's high-level
        # click path, which handles the cross-origin focus handshake so the
        # iframe window becomes focused alongside the input — subsequent
        # page.keyboard.type() then delivers isTrusted keystrokes the SDK
        # accepts. Target by data-fieldtype (stable per Adyen SDK) rather
        # than .first, which can match the wrong element if Adyen inserts
        # hidden sibling inputs.
        iframe_selector = f'span[data-cse="{cse_field}"] iframe'
        input_selector = f'input[data-fieldtype="{cse_field}"]'
        try:
            frame: FrameLocator = self.page.frame_locator(iframe_selector)
            input_el = frame.locator(input_selector)
            await input_el.wait_for(state="visible", timeout=10_000)
            await input_el.click(timeout=5_000)
            await self.page.keyboard.type(value, delay=_KEYSTROKE_DELAY_MS)
            self.log.info("%s entered", label)
        except Exception as e:
            raise PaymentFailed(f"failed to fill {label} iframe: {e}") from e
        await self._log_adyen_state(after=label)

    async def _submit(self) -> None:
        await self._log_adyen_state()
        try:
            await self.page.locator(self.PLACE_ORDER).click(timeout=10_000)
            self.log.info("Place-order clicked")
        except Exception as e:
            raise PaymentFailed(f"could not click place-order: {e}") from e

    async def _log_adyen_state(self, *, after: str | None = None) -> None:
        # Adyen mirrors its component validation into this hidden input on
        # every keystroke. Logging it after each field (and before submit)
        # makes "place-order succeeded but payment failed" easy to diagnose.
        tag = f" after {after}" if after else ""
        try:
            raw = await self.page.locator(self.PAYMENT_STATE).input_value(timeout=2_000)
            state = json.loads(raw)
        except Exception as e:
            self.log.warning("Could not read Adyen payment state%s: %s", tag, e)
            return
        valid_map = state.get("valid") or {}
        if state.get("isValid"):
            self.log.info("Adyen state%s: isValid=true (valid=%s)", tag, valid_map)
            return
        invalid = [k for k, v in valid_map.items() if v is False]
        self.log.warning(
            "Adyen state%s: isValid=false (valid=%s, failing=%s)",
            tag, valid_map, invalid or "unknown",
        )

    async def _await_confirmation(self, timeout_seconds: int) -> None:
        try:
            await self.page.get_by_text(self.CONFIRMATION_TEXT).wait_for(
                state="visible", timeout=timeout_seconds * 1_000
            )
            self.log.info("Order confirmed")
            return
        except Exception:
            self.log.warning("No confirmation message; checking for retry button")

        try:
            await self.page.locator(f"xpath={self.RETRY_PAYMENT}").click(timeout=5_000)
            raise PaymentFailed("payment retry button appeared")
        except PaymentFailed:
            raise
        except Exception as e:
            raise PaymentFailed(
                "no confirmation and no retry button after payment submit"
            ) from e
