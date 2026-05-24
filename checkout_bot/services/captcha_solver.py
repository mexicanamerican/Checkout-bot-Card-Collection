from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from patchright.async_api import Page


CAPSOLVER_URL = "https://api.capsolver.com"

# Cloudflare hidden input that holds the Turnstile response token.
_TOKEN_INJECTION_JS = """
(token) => {
    const input = document.querySelector('input[name="cf-turnstile-response"]');
    if (input) { input.value = token; return true; }
    return false;
}
"""


class CaptchaError(Exception):
    """Raised when CAPTCHA solving fails or times out."""


class CapSolverClient:
    """Async client for CapSolver's Cloudflare Turnstile endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        poll_interval_seconds: float = 2.0,
        poll_max_attempts: int = 60,
        logger: logging.Logger | logging.LoggerAdapter | None = None,
    ) -> None:
        self._api_key = api_key
        self._poll_interval = poll_interval_seconds
        self._poll_max_attempts = poll_max_attempts
        self._log = logger or logging.getLogger(__name__)

    async def solve_turnstile(self, page: Page, site_url: str, site_key: str) -> None:
        """Solve Turnstile for the given page and inject the token into the DOM."""
        async with httpx.AsyncClient(timeout=30) as client:
            task_id = await self._create_task(client, site_url, site_key)
            solution = await self._wait_for_solution(client, task_id)

        token = solution.get("token")
        if not token:
            raise CaptchaError("CapSolver returned no token")

        injected = await page.evaluate(_TOKEN_INJECTION_JS, token)
        if not injected:
            self._log.warning("Turnstile hidden input not found; token not injected")
        else:
            self._log.info("Turnstile token injected")

    async def _create_task(
        self, client: httpx.AsyncClient, site_url: str, site_key: str
    ) -> str:
        payload = {
            "clientKey": self._api_key,
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": site_url,
                "websiteKey": site_key,
            },
        }
        response = await client.post(f"{CAPSOLVER_URL}/createTask", json=payload)
        response.raise_for_status()
        data = response.json()
        task_id = data.get("taskId")
        if not task_id:
            raise CaptchaError(f"CapSolver createTask failed: {data}")
        return task_id

    async def _wait_for_solution(
        self, client: httpx.AsyncClient, task_id: str
    ) -> dict[str, Any]:
        for attempt in range(self._poll_max_attempts):
            response = await client.post(
                f"{CAPSOLVER_URL}/getTaskResult",
                json={"clientKey": self._api_key, "taskId": task_id},
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status == "ready":
                return data["solution"]
            if status == "failed" or data.get("errorId"):
                raise CaptchaError(f"CapSolver task failed: {data}")
            await asyncio.sleep(self._poll_interval)

        raise CaptchaError(
            f"CapSolver did not return a solution within {self._poll_max_attempts} attempts"
        )
