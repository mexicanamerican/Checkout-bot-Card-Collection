from __future__ import annotations

from checkout_bot.config import TaskRow
from checkout_bot.core.exceptions import FormFillFailed
from checkout_bot.pages.base_page import BasePage
from checkout_bot.services.province_lookup import get_province_code
from checkout_bot.utils.random_data import random_phone_number, random_string


class CheckoutFormPage(BasePage):
    """Billing/shipping form on the ToysCenter checkout page."""

    FIRST_NAME = '[id="billing.first_name"]'
    LAST_NAME = '[id="billing.last_name"]'
    ADDRESS_1 = '[id="billing.address_1"]'
    ADDRESS_2 = '[id="billing.address_2"]'
    POSTCODE = '[id="billing.postcode"]'
    CITY = '[id="billing.city"]'
    PHONE = '[id="billing.phone"]'
    EMAIL = "#billing_email"
    # The page renders multiple Choices.js widgets (customer type, billing
    # province, optional shipping province). Scope to the billing state's
    # wrapper so we don't hit the wrong dropdown.
    PROVINCE_WRAPPER_CANDIDATES = (
        '.choices:has(select[name="billing.state"])',
        '.choices:has(select[id="billing.state"])',
        '.choices:has(select[name="billing[state]"])',
    )
    PROVINCE_INNER = ".choices__inner"
    PROVINCE_OPTION_TEMPLATE = (
        "div.choices__item.choices__item--choice.choices__item--selectable"
        '[data-value="{code}"]'
    )
    NEXT_BUTTON = '//*[@id="step_address_buttons"]/button'

    async def fill_and_submit(self, task: TaskRow) -> None:
        try:
            await self._fill_personal_info(task)
            await self._fill_address(task)
            await self._select_province(task.state)
            await self._fill_contact(task)
            await self.page.locator(f"xpath={self.NEXT_BUTTON}").click()
            self.log.info("Address form submitted")
        except Exception as e:
            raise FormFillFailed(str(e)) from e

    async def _fill_personal_info(self, task: TaskRow) -> None:
        # Note: original code randomizes first name despite reading it from CSV.
        # Preserved intentionally — see plan "Open question".
        await self.page.locator(self.FIRST_NAME).fill(random_string())
        await self.page.locator(self.LAST_NAME).fill(task.surname)

    async def _fill_address(self, task: TaskRow) -> None:
        # Same intentional randomization on address_1.
        line1 = f"{random_string()} {task.address_line_1[:-2]}"
        await self.page.locator(self.ADDRESS_1).fill(line1)
        await self.page.locator(self.ADDRESS_2).fill(task.address_line_1[-2:])
        await self.page.locator(self.POSTCODE).fill(task.zipcode)
        await self.page.locator(self.CITY).fill(task.city)

    async def _select_province(self, state: str) -> None:
        code = get_province_code(state)
        wrapper = await self._find_province_wrapper()
        await wrapper.locator(self.PROVINCE_INNER).first.click()
        # Options render in a portal-like dropdown list that is appended to the
        # same wrapper, so scope the option click to it as well.
        await wrapper.locator(
            self.PROVINCE_OPTION_TEMPLATE.format(code=code)
        ).first.click()

    async def _find_province_wrapper(self):
        for selector in self.PROVINCE_WRAPPER_CANDIDATES:
            locator = self.page.locator(selector)
            if await locator.count() > 0:
                return locator.first
        # Fallback: pick the Choices.js wrapper whose visible text starts with
        # "Provincia" — works regardless of the underlying select's name/id.
        fallback = self.page.locator(
            '.choices:has(.choices__inner:has-text("Provincia"))'
        )
        if await fallback.count() == 0:
            raise FormFillFailed("Province dropdown wrapper not found")
        return fallback.first

    async def _fill_contact(self, task: TaskRow) -> None:
        await self.page.locator(self.PHONE).fill(random_phone_number())
        # Original mixes random local-part with the domain portion of the CSV email.
        await self.page.locator(self.EMAIL).fill(random_string() + task.email[6:])
