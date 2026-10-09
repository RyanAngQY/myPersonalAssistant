from datetime import datetime
from zoneinfo import ZoneInfo

import dateparser


def parse_when(text: str, timezone: ZoneInfo) -> datetime | None:
    """Parse user input as a timezone-aware local datetime."""
    value = dateparser.parse(text, settings={
        "TIMEZONE": str(timezone), "TO_TIMEZONE": str(timezone),
        "RETURN_AS_TIMEZONE_AWARE": True, "PREFER_DATES_FROM": "future",
    })
    return value.astimezone(timezone) if value else None


def parse_importance(value: str) -> int | None:
    values = {"low": 1, "l": 1, "medium": 2, "med": 2, "m": 2, "high": 3, "h": 3}
    return values.get(value.strip().lower())
