from __future__ import annotations

import random
import string


def random_string(min_len: int = 5, max_len: int = 10) -> str:
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_letters, k=length))


def random_phone_number(length: int = 10) -> str:
    return "".join(random.choices(string.digits, k=length))
