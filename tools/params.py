"""Parsing of tool parameters shared by the list and search tools."""

from typing import Any

# Box API maximums: GET /folders/{id}/items accepts limit <= 1000, GET /search accepts limit <= 200.
LIST_LIMIT_MAX = 1000
SEARCH_LIMIT_MAX = 200


def parse_limit(value: Any, default: int, maximum: int) -> int:
    """The ``limit`` parameter as an int clamped to 1..maximum; ``default`` when it is empty.

    Accepts numbers and numeric strings such as "20" or "20.0" (an LLM may fill the
    parameter with either). Raises ValueError for anything else.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    if isinstance(value, bool):
        raise ValueError(f"limit must be a whole number, got {value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"limit must be a whole number, got {value!r}") from None
    if not number.is_integer():
        raise ValueError(f"limit must be a whole number, got {value!r}")
    return max(1, min(int(number), maximum))
