"""
Numerology layer — pure date arithmetic, no ephemeris.
"""

from datetime import date


def reduce(n: int, keep_masters: bool = True) -> int:
    """Reduce to single digit; keep 11, 22, 33 as master numbers if keep_masters."""
    while n > 9 and not (keep_masters and n in (11, 22, 33)):
        n = sum(int(d) for d in str(n))
    return n


def life_path(birth_date: date) -> int:
    """Classic reduction of month + day + year (each reduced separately)."""
    m = reduce(birth_date.month)
    d = reduce(birth_date.day)
    y = reduce(sum(int(c) for c in str(birth_date.year)))
    return reduce(m + d + y)


def _reference_year(birth_date: date, on_date: date) -> int:
    """
    The personal year runs birthday to birthday: it is calculated from the
    calendar year of the person's MOST RECENT birthday, not the current
    calendar year. E.g. birthday Oct 16 — on July 19 2026 the last birthday
    was Oct 16 2025, so the personal year uses 2025.
    """
    if (on_date.month, on_date.day) >= (birth_date.month, birth_date.day):
        return on_date.year
    return on_date.year - 1


def personal_year(birth_date: date, on_date: date) -> int:
    """Personal year = birth month + birth day + year of last birthday (reduced)."""
    ref = _reference_year(birth_date, on_date)
    m = reduce(birth_date.month)
    d = reduce(birth_date.day)
    y = reduce(sum(int(c) for c in str(ref)))
    return reduce(m + d + y)


def personal_month(birth_date: date, on_date: date) -> int:
    py = personal_year(birth_date, on_date)
    return reduce(py + on_date.month)


def personal_day(birth_date: date, on_date: date) -> int:
    pm = personal_month(birth_date, on_date)
    return reduce(pm + on_date.day)


def numerology_report(birth_date: date, today: date = None) -> dict:
    if today is None:
        today = date.today()
    return {
        "life_path": life_path(birth_date),
        "personal_year": personal_year(birth_date, today),
        "personal_month": personal_month(birth_date, today),
        "personal_day": personal_day(birth_date, today),
    }
