from __future__ import annotations

import asyncio

from patchright.async_api import Error as PlaywrightError
from patchright._impl._errors import TargetClosedError

from checkout_bot.config import AppSettings, TaskRow, load_tasks
from checkout_bot.core.browser import launch_page
from checkout_bot.core.exceptions import CheckoutError
from checkout_bot.core.sleep_prevention import prevent_system_sleep
from checkout_bot.pages.cart_page import CartPage
from checkout_bot.pages.checkout_form_page import CheckoutFormPage
from checkout_bot.pages.payment_page import PaymentPage
from checkout_bot.pages.product_page import ProductPage
from checkout_bot.pages.shipping_step_page import ShippingStepPage
from checkout_bot.services.captcha_solver import CapSolverClient
from checkout_bot.utils.logging import get_logger, setup_logging


async def run() -> None:
    settings = AppSettings.load()
    setup_logging(settings.log_level)
    log = get_logger("checkout_bot")
    log.info("Loaded settings; reading tasks from %s", settings.tasks_csv_path)

    tasks = load_tasks(settings.tasks_csv_path)
    log.info("Loaded %d task(s); max concurrency=%d", len(tasks), settings.max_concurrency)

    # On Ctrl+C, patchright's pending internal waits surface as orphan
    # TargetClosedError / connection-closed futures. Mute them so shutdown
    # output stays clean; surface anything unexpected.
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_quiet_shutdown_exception_handler)

    sem = asyncio.Semaphore(settings.max_concurrency)
    with prevent_system_sleep():
        await asyncio.gather(
            *(_run_task(t, idx + 1, sem, settings) for idx, t in enumerate(tasks))
        )


def _quiet_shutdown_exception_handler(
    loop: asyncio.AbstractEventLoop, context: dict
) -> None:
    exc = context.get("exception")
    if isinstance(exc, (TargetClosedError, PlaywrightError, asyncio.CancelledError)):
        return
    if isinstance(exc, Exception) and "Connection closed" in str(exc):
        return
    loop.default_exception_handler(context)


async def _run_task(
    task: TaskRow,
    task_id: int,
    sem: asyncio.Semaphore,
    settings: AppSettings,
) -> None:
    log = get_logger("checkout_bot.task", task_id=task_id)
    async with sem:
        while True:
            log.info("Starting attempt for %s", task.product_link)
            try:
                await _execute_checkout(task, task_id, settings)
                log.info("Checkout completed successfully")
                return
            except (asyncio.CancelledError, KeyboardInterrupt):
                log.info("Task cancelled — stopping")
                raise
            except TargetClosedError as e:
                log.warning("Browser/page closed (%s) — restarting in %ss",
                            e.message, settings.restart_delay_seconds)
                await asyncio.sleep(settings.restart_delay_seconds)
            except CheckoutError as e:
                log.warning("Attempt failed: %s — retrying in %ss",
                            e, settings.restart_delay_seconds)
                await asyncio.sleep(settings.restart_delay_seconds)
            except PlaywrightError as e:
                log.warning("Playwright error: %s — retrying in %ss",
                            e.message, settings.restart_delay_seconds)
                await asyncio.sleep(settings.restart_delay_seconds)
            except Exception:
                log.exception("Unexpected error — retrying in %ss",
                              settings.restart_delay_seconds)
                await asyncio.sleep(settings.restart_delay_seconds)


async def _execute_checkout(
    task: TaskRow, task_id: int, settings: AppSettings
) -> None:
    log = get_logger("checkout_bot.task", task_id=task_id)
    captcha = CapSolverClient(
        settings.capsolver_api_key,
        poll_interval_seconds=settings.captcha_poll_interval_seconds,
        poll_max_attempts=settings.captcha_poll_max_attempts,
        logger=log,
    )

    async with launch_page(settings) as page:
        ctx = {
            "page": page,
            "captcha_solver": captcha,
            "site_key": settings.toys_center_site_key,
            "logger": log,
        }

        product = ProductPage(**ctx)
        await product.open(str(task.product_link))
        await product.wait_for_availability(settings.refresh_interval_seconds)
        await product.add_to_cart()
        await product.go_to_cart()

        cart = CartPage(**ctx)
        await cart.proceed_to_checkout()

        shipping = ShippingStepPage(**ctx)
        await shipping.select_and_continue()

        form = CheckoutFormPage(**ctx)
        await form.fill_and_submit(task)

        payment = PaymentPage(**ctx)
        await payment.pay(task, settings.payment_confirmation_timeout_seconds)
