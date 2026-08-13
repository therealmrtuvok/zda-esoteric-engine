"""
ephemeris-core: single source of truth for planetary positions.
Input: datetime (UTC) + lat/lon. Output: ecliptic longitudes, speeds,
ascendant, MC, house cusps.
Nothing else in this project imports swisseph directly.
"""

import os
import swisseph as swe
from dataclasses import dataclass, field
from typing import Optional

# kerykeion ships the seas_18.se1 asteroid file; use it as the ephe path
_KERYKEION_SWEPH = os.path.join(
    os.path.dirname(__file__),
    "../../.venv/lib/python3.14/site-packages/kerykeion/sweph",
)
_FALLBACK_SWEPH = os.path.join(
    os.path.expanduser("~"),
    "Library/Python/3.14/lib/python/site-packages/kerykeion/sweph",
)
# Support override via env var, then kerykeion bundle, then system default
EPHE_PATH = os.environ.get(
    "EPHE_PATH",
    None,
)

def _find_ephe_path() -> str:
    if EPHE_PATH:
        return EPHE_PATH
    for pkg_root in (
        "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages",
        os.path.expanduser("~/Library/Python/3.14/lib/python/site-packages"),
    ):
        candidate = os.path.join(pkg_root, "kerykeion", "sweph")
        if os.path.isdir(candidate):
            return candidate
    return "/usr/share/swisseph"  # system fallback


_EPHE_PATH = _find_ephe_path()

# Swiss Ephemeris planet IDs
_PLANET_IDS = {
    "sun":       swe.SUN,
    "moon":      swe.MOON,
    "mercury":   swe.MERCURY,
    "venus":     swe.VENUS,
    "mars":      swe.MARS,
    "jupiter":   swe.JUPITER,
    "saturn":    swe.SATURN,
    "uranus":    swe.URANUS,
    "neptune":   swe.NEPTUNE,
    "pluto":     swe.PLUTO,
    "true_node": swe.TRUE_NODE,
    "chiron":    swe.CHIRON,
    "juno":      swe.AST_OFFSET + 3,
}

_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


@dataclass
class Planet:
    name: str
    longitude: float   # 0–360 ecliptic
    latitude: float
    distance: float
    speed: float       # deg/day; negative = retrograde
    retrograde: bool


@dataclass
class ChartData:
    julian_day: float
    planets: dict           # name → Planet
    ascendant: float        # ecliptic longitude of Asc
    mc: float               # ecliptic longitude of MC
    armc: float
    houses_placidus: list   # 12 cusp longitudes (1st … 12th)
    houses_whole_sign: list # 12 cusp longitudes for Whole Sign


def calc_chart(year: int, month: int, day: int, hour_ut: float,
               lat: float, lon: float) -> ChartData:
    """
    year/month/day: calendar date
    hour_ut: decimal hours in UTC (e.g. 5 + 24/60 = 5.4)
    lat: degrees north positive
    lon: degrees east positive (west is negative)
    """
    swe.set_ephe_path(_EPHE_PATH)
    jd = swe.julday(year, month, day, hour_ut)

    planets = {}
    for name, pid in _PLANET_IDS.items():
        result, _flag = swe.calc_ut(jd, pid, _FLAGS)
        lon_val, lat_val, dist, spd, *_ = result
        planets[name] = Planet(
            name=name,
            longitude=lon_val % 360,
            latitude=lat_val,
            distance=dist,
            speed=spd,
            retrograde=spd < 0,
        )

    cusps_p, ascmc_p = swe.houses(jd, lat, lon, b"P")
    cusps_w, ascmc_w = swe.houses(jd, lat, lon, b"W")

    # cusps are 1-indexed in pyswisseph; ascmc[0]=Asc, ascmc[1]=MC
    return ChartData(
        julian_day=jd,
        planets=planets,
        ascendant=ascmc_p[0],
        mc=ascmc_p[1],
        armc=ascmc_p[2],
        houses_placidus=list(cusps_p),      # 12 elements, 0-indexed (cusps[0] = 1st house = Asc)
        houses_whole_sign=list(cusps_w),
    )


def calc_at_jd(jd: float) -> dict:
    """Return planet longitudes (and speeds) for an arbitrary Julian Day."""
    swe.set_ephe_path(_EPHE_PATH)
    out = {}
    for name, pid in _PLANET_IDS.items():
        result, _ = swe.calc_ut(jd, pid, _FLAGS)
        lon_val, _, _, spd, *_ = result
        out[name] = {"longitude": lon_val % 360, "speed": spd, "retrograde": spd < 0}
    return out


def calc_chart_at_jd(jd: float, lat: float, lon: float) -> ChartData:
    """Full chart (planets + houses) for an arbitrary Julian Day."""
    swe.set_ephe_path(_EPHE_PATH)
    y, m, d, h = swe.revjul(jd)
    return calc_chart(y, m, d, h, lat, lon)


def julian_day(year: int, month: int, day: int, hour_ut: float = 0.0) -> float:
    swe.set_ephe_path(_EPHE_PATH)
    return swe.julday(year, month, day, hour_ut)


def jd_to_datetime_tuple(jd: float) -> tuple:
    """Return (year, month, day, hour_ut_decimal) for a Julian Day."""
    swe.set_ephe_path(_EPHE_PATH)
    return swe.revjul(jd)


def binary_search_body_longitude(body: str, target_lon: float,
                                  jd_start: float, jd_end: float,
                                  tolerance: float = 1e-7) -> float:
    """
    Find the JD in [jd_start, jd_end] where `body`'s longitude equals
    target_lon. The window must bracket exactly one crossing and the body's
    motion must be monotonic across it (true for Sun/Moon over their windows).
    """
    swe.set_ephe_path(_EPHE_PATH)
    pid = _PLANET_IDS[body]

    def body_lon(jd):
        r, _ = swe.calc_ut(jd, pid, _FLAGS)
        return r[0] % 360

    def angular_diff(a, b):
        d = (a - b) % 360
        if d > 180:
            d -= 360
        return d

    for _ in range(80):
        mid = (jd_start + jd_end) / 2
        diff = angular_diff(body_lon(mid), target_lon)
        if abs(diff) < tolerance:
            return mid
        if diff > 0:
            jd_end = mid
        else:
            jd_start = mid
    return (jd_start + jd_end) / 2


def find_next_crossing(body: str, target_lon: float, jd_from: float,
                        max_days: float = 400.0, step_days: float = 0.5) -> float:
    """
    Scan forward from jd_from for the next instant `body` crosses target_lon
    (in the direction of increasing longitude), then bisect to precision.
    Handles the 0°/360° wrap. Suitable for Sun/Moon returns.
    """
    swe.set_ephe_path(_EPHE_PATH)
    pid = _PLANET_IDS[body]

    def body_lon(jd):
        r, _ = swe.calc_ut(jd, pid, _FLAGS)
        return r[0] % 360

    def signed_diff(jd):
        d = (body_lon(jd) - target_lon) % 360
        if d > 180:
            d -= 360
        return d

    prev_jd = jd_from
    prev_d = signed_diff(prev_jd)
    jd = jd_from + step_days
    end = jd_from + max_days
    while jd <= end:
        d = signed_diff(jd)
        # crossing: signed diff goes from negative to non-negative without a wrap jump
        if prev_d < 0 <= d and (d - prev_d) < 180:
            return binary_search_body_longitude(body, target_lon, prev_jd, jd)
        prev_jd, prev_d = jd, d
        jd += step_days
    raise ValueError(f"No {body} crossing of {target_lon}° within {max_days} days")


def binary_search_sun_longitude(target_lon: float, jd_start: float, jd_end: float,
                                 tolerance: float = 1e-6) -> float:
    """
    Find the Julian Day between jd_start and jd_end where the Sun's longitude
    equals target_lon (modular, handles 0°/360° wrap).
    Used to find the Design date (Sun = natal Sun − 88°).
    """
    swe.set_ephe_path(_EPHE_PATH)

    def sun_lon(jd):
        r, _ = swe.calc_ut(jd, swe.SUN, _FLAGS)
        return r[0] % 360

    def angular_diff(a, b):
        d = (a - b) % 360
        if d > 180:
            d -= 360
        return d

    for _ in range(60):
        mid = (jd_start + jd_end) / 2
        diff = angular_diff(sun_lon(mid), target_lon)
        if abs(diff) < tolerance:
            return mid
        if diff > 0:
            jd_end = mid
        else:
            jd_start = mid

    return (jd_start + jd_end) / 2
