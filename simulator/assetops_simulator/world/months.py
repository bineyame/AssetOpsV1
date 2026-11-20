"""Calendar months as `YYYY-MM` text (spec §4.1). Named `months`, not `calendar`, so
the standard library module it uses is not shadowed (R23)."""

from __future__ import annotations

import calendar
from datetime import date

MONTH_ABBR = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def parse_month(month: str) -> tuple[int, int]:
    year, number = month.split("-")
    if len(year) != 4 or len(number) != 2:
        raise ValueError(month)
    return int(year), int(number)


def days_in(month: str) -> int:
    year, number = parse_month(month)
    return calendar.monthrange(year, number)[1]


def period_end(month: str) -> date:
    year, number = parse_month(month)
    return date(year, number, days_in(month))


def dates_of(month: str) -> list[date]:
    year, number = parse_month(month)
    return [date(year, number, day) for day in range(1, days_in(month) + 1)]


def next_month(month: str) -> str:
    year, number = parse_month(month)
    year, number = (year + 1, 1) if number == 12 else (year, number + 1)
    return f"{year:04d}-{number:02d}"


def day_class(day: date, day_classes: dict) -> str | None:
    """The class whose ISO weekdays include this date's, or None if none does."""
    weekday = day.isoweekday()
    for name in sorted(day_classes):
        if weekday in day_classes[name]:
            return name
    return None
