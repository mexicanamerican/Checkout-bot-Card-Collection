from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class AppSettings(BaseModel):
    """Validated runtime configuration loaded from .env."""

    capsolver_api_key: str = Field(min_length=1)
    toys_center_site_key: str = Field(min_length=1)

    tasks_csv_path: Path = Path("tasks/toyscenter.csv")
    max_concurrency: int = Field(default=10, ge=1)
    refresh_interval_seconds: float = Field(default=2.0, gt=0)
    restart_delay_seconds: float = Field(default=10.0, ge=0)
    headless: bool = False
    log_level: str = "INFO"
    payment_confirmation_timeout_seconds: int = Field(default=60, gt=0)
    captcha_poll_max_attempts: int = Field(default=60, ge=1)
    captcha_poll_interval_seconds: float = Field(default=2.0, gt=0)

    @classmethod
    def load(cls, *, project_root: Path | None = None) -> "AppSettings":
        root = project_root or Path(__file__).resolve().parents[2]
        load_dotenv(root / ".env")

        try:
            return cls(
                capsolver_api_key=os.environ.get("CAPSOLVER_API_KEY", ""),
                toys_center_site_key=os.environ.get("TOYS_CENTER_KEY", ""),
                tasks_csv_path=root / "tasks" / "toyscenter.csv",
            )
        except ValidationError as e:
            raise RuntimeError(
                "Invalid configuration. Check .env "
                "(CAPSOLVER_API_KEY and TOYS_CENTER_KEY required).\n"
                f"{e}"
            ) from e
