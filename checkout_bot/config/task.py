from __future__ import annotations

import csv
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


_EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])/\d{2}$")


class TaskRow(BaseModel):
    """A single validated CSV row driving one checkout attempt."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    product_link: HttpUrl
    email: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    address_line_1: str = Field(min_length=1)
    city: str = Field(min_length=1)
    state: str = Field(min_length=1)
    zipcode: str = Field(min_length=1)

    titolare_carta: str = Field(min_length=1)
    numero_carta: str = Field(min_length=12)
    scadenza_carta: str
    cvv: str = Field(min_length=3, max_length=4)

    @field_validator("numero_carta")
    @classmethod
    def _digits_only(cls, v: str) -> str:
        digits = v.replace(" ", "")
        if not digits.isdigit():
            raise ValueError("numero_carta must contain only digits")
        return digits

    @field_validator("scadenza_carta")
    @classmethod
    def _expiry_format(cls, v: str) -> str:
        if not _EXPIRY_RE.match(v):
            raise ValueError("scadenza_carta must be MM/YY")
        return v

    @field_validator("cvv")
    @classmethod
    def _cvv_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("cvv must be digits only")
        return v


def load_tasks(csv_path: Path) -> list[TaskRow]:
    """Read and validate every CSV row. Raises with a readable error on bad rows."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"tasks CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    tasks: list[TaskRow] = []
    errors: list[str] = []
    for i, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            tasks.append(TaskRow(**row))
        except ValidationError as e:
            errors.append(f"row {i}: {e}")

    if errors:
        raise ValueError("Invalid tasks CSV:\n" + "\n".join(errors))
    if not tasks:
        raise ValueError(f"tasks CSV is empty: {csv_path}")
    return tasks
