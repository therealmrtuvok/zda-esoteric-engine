"""
Derived astrology charts — all consume ephemeris_core, never swisseph.
Secondary progressions, solar/lunar returns, annual profections,
synastry, composite, transits.
"""

from datetime import date

from .ephemeris_core import (
    calc_chart,
    calc_at_jd,
    calc_chart_at_jd,
    julian_day,
    jd_to_datetime_tuple,
    find_next_crossing,
)
from .astrology import (
    SIGNS,
    longitude_to_sign_degree,
    whole_sign_house,
    ASPECTS,
    ASPECT_SYMBOLS,
)

TROPICAL_YEAR = 365.24219  # days


# ---------------------------------------------------------------------------
# Secondary progressions — day-for-a-year
# ---------------------------------------------------------------------------
def progressed_positions(birth_jd: float, target_jd: float) -> dict:
    """
    Positions at birth_jd + elapsed_years (in days): each day after birth
    stands for one year of life.
    """
    elapsed_years = (target_jd - birth_jd) / TROPICAL_YEAR
    prog_jd = birth_jd + elapsed_years
    positions = calc_at_jd(prog_jd)
    return {"progressed_jd": prog_jd, "elapsed_years": elapsed_years,
            "positions": positions}


# ---------------------------------------------------------------------------
# Solar / lunar returns
# ---------------------------------------------------------------------------
def solar_return(natal_sun_lon: float, target_year: int,
                 lat: float, lon: float,
                 birth_month: int, birth_day: int):
    """
    Chart for the instant the transiting Sun returns to its exact natal
    longitude in target_year. Search starts a few days before the birthday.
    """
    start_jd = julian_day(target_year, birth_month, max(birth_day - 4, 1))
    return_jd = find_next_crossing("sun", natal_sun_lon, start_jd, max_days=10)
    return return_jd, calc_chart_at_jd(return_jd, lat, lon)


def lunar_return(natal_moon_lon: float, from_jd: float,
                 lat: float, lon: float):
    """
    Chart for the next instant (after from_jd) the transiting Moon returns
    to its exact natal longitude. Recurs roughly every 27.3 days.
    """
    return_jd = find_next_crossing("moon", natal_moon_lon, from_jd,
                                   max_days=29, step_days=0.1)
    return return_jd, calc_chart_at_jd(return_jd, lat, lon)


# ---------------------------------------------------------------------------
# Annual profections — pure house arithmetic, Whole Sign
# ---------------------------------------------------------------------------
TRADITIONAL_RULERS = {
    "Aries": "Mars",       "Taurus": "Venus",   "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",        "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",   "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}


def completed_age(birth: date, on_date: date) -> int:
    age = on_date.year - birth.year
    if (on_date.month, on_date.day) < (birth.month, birth.day):
        age -= 1
    return age


def annual_profection(asc_longitude: float, birth: date, on_date: date) -> dict:
    """
    Profected house = (age % 12) + 1 counted from the Ascendant sign
    (Whole Sign). The sign on that house is the year's focus; its
    traditional ruler is the Lord of the Year.
    """
    age = completed_age(birth, on_date)
    house = (age % 12) + 1
    asc_sign_idx = int(asc_longitude % 360 / 30)
    profected_sign = SIGNS[(asc_sign_idx + house - 1) % 12]
    return {
        "age": age,
        "profected_house": house,
        "profected_sign": profected_sign,
        "lord_of_year": TRADITIONAL_RULERS[profected_sign],
    }


# ---------------------------------------------------------------------------
# Synastry — cross-aspect grid between two position sets
# ---------------------------------------------------------------------------
def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def synastry_aspects(positions_a: dict, positions_b: dict) -> list[dict]:
    """
    Aspect grid: every planet of person A against every planet of person B.
    positions_*: dict of planet_name → {"longitude": float, ...}
    """
    out = []
    for name_a, pa in positions_a.items():
        for name_b, pb in positions_b.items():
            diff = _angular_distance(pa["longitude"], pb["longitude"])
            for asp_name, exact, orb in ASPECTS:
                if abs(diff - exact) <= orb:
                    out.append({
                        "a": name_a, "b": name_b,
                        "aspect": asp_name,
                        "symbol": ASPECT_SYMBOLS[asp_name],
                        "orb": round(abs(diff - exact), 2),
                    })
                    break
    return out


# ---------------------------------------------------------------------------
# Composite — circular midpoints
# ---------------------------------------------------------------------------
def circular_midpoint(a: float, b: float) -> float:
    """Midpoint along the SHORT arc between two longitudes (0–360 safe)."""
    a %= 360
    b %= 360
    d = (b - a) % 360
    if d > 180:
        # short arc runs the other way
        return (b + (360 - d) / 2) % 360
    return (a + d / 2) % 360


def composite_positions(positions_a: dict, positions_b: dict) -> dict:
    """Composite chart positions: circular midpoint of each planet pair."""
    out = {}
    for name in positions_a:
        if name in positions_b:
            out[name] = {
                "longitude": circular_midpoint(
                    positions_a[name]["longitude"],
                    positions_b[name]["longitude"],
                )
            }
    return out


# ---------------------------------------------------------------------------
# Transits — positions now vs natal
# ---------------------------------------------------------------------------
def transit_aspects_to_natal(natal_positions: dict, transit_jd: float) -> dict:
    """Current sky vs natal chart: transiting positions + aspect list."""
    transiting = calc_at_jd(transit_jd)
    aspects = synastry_aspects(
        {("t_" + k): v for k, v in transiting.items()},
        natal_positions,
    )
    return {"transiting": transiting, "aspects": aspects}
