from __future__ import annotations


class CheckoutError(Exception):
    """Base error for any failure during a checkout attempt. Caught and retried."""


class MonitoringFailed(CheckoutError):
    """Product monitoring failed (cart click, popup, navigation)."""


class FormFillFailed(CheckoutError):
    """Filling the shipping/billing form failed."""


class PaymentFailed(CheckoutError):
    """Payment was submitted but no confirmation was received, or retry button appeared."""


class CaptchaFailed(CheckoutError):
    """CAPTCHA solving failed beyond retries."""


class BrowserClosed(CheckoutError):
    """Browser, context or page was closed unexpectedly mid-operation."""
