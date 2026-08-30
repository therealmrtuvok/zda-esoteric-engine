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


# ---------------------------------------------------------------------------
# Sky events: stations, lunations, ingresses, eclipses.
#
# These live here because of the one architectural rule: this is the only file
# that imports swisseph. sky_events.py turns these raw instants into labelled,
# dated events. Nothing here knows what an event means.
# ---------------------------------------------------------------------------

ECLIPSE_KINDS = {
    swe.ECL_TOTAL: "total",
    swe.ECL_ANNULAR: "annular",
    swe.ECL_PARTIAL: "partial",
    swe.ECL_ANNULAR_TOTAL: "hybrid",
    swe.ECL_PENUMBRAL: "penumbral",
}


def _body_speed(pid: int, jd: float) -> float:
    r, _ = swe.calc_ut(jd, pid, _FLAGS)
    return r[3]


def _body_lon(pid: int, jd: float) -> float:
    r, _ = swe.calc_ut(jd, pid, _FLAGS)
    return r[0] % 360


def find_stations(body: str, jd_from: float, jd_to: float,
                  step_days: float = 1.0) -> list[dict]:
    """
    Instants in [jd_from, jd_to] where `body` changes apparent direction.
    Returns [{"jd", "direction", "longitude"}] with direction "retrograde"
    when the body is turning backward and "direct" when it is turning forward.

    The Sun and Moon never station, so they are rejected rather than silently
    returning an empty list, which would hide a caller's mistake.
    """
    if body in ("sun", "moon"):
        raise ValueError(f"{body} never stations")
    swe.set_ephe_path(_EPHE_PATH)
    pid = _PLANET_IDS[body]

    out = []
    prev_jd = jd_from
    prev_v = _body_speed(pid, prev_jd)
    jd = jd_from + step_days
    while jd <= jd_to:
        v = _body_speed(pid, jd)
        if (prev_v < 0) != (v < 0):
            lo, hi = prev_jd, jd
            for _ in range(60):
                mid = (lo + hi) / 2
                if (_body_speed(pid, mid) < 0) == (prev_v < 0):
                    lo = mid
                else:
                    hi = mid
            exact = (lo + hi) / 2
            out.append({
                "jd": exact,
                "direction": "retrograde" if v < 0 else "direct",
                "longitude": _body_lon(pid, exact),
            })
        prev_jd, prev_v = jd, v
        jd += step_days
    return out


def find_lunations(jd_from: float, jd_to: float) -> list[dict]:
    """
    New and full moons in [jd_from, jd_to], found by bisecting the Moon's
    elongation from the Sun across 0 degrees (new) and 180 degrees (full).
    Returns [{"jd", "phase", "longitude"}] where longitude is the Moon's.
    """
    swe.set_ephe_path(_EPHE_PATH)
    moon, sun = _PLANET_IDS["moon"], _PLANET_IDS["sun"]

    def elong(jd):
        return (_body_lon(moon, jd) - _body_lon(sun, jd)) % 360

    def signed(jd, target):
        d = (elong(jd) - target) % 360
        return d - 360 if d > 180 else d

    out = []
    for target, phase in ((0.0, "new"), (180.0, "full")):
        prev_jd = jd_from
        prev_d = signed(prev_jd, target)
        jd = jd_from + 0.5
        while jd <= jd_to:
            d = signed(jd, target)
            if prev_d < 0 <= d and (d - prev_d) < 180:
                lo, hi = prev_jd, jd
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if signed(mid, target) < 0:
                        lo = mid
                    else:
                        hi = mid
                exact = (lo + hi) / 2
                out.append({"jd": exact, "phase": phase,
                            "longitude": _body_lon(moon, exact)})
            prev_jd, prev_d = jd, d
            jd += 0.5
    out.sort(key=lambda e: e["jd"])
    return out


def find_sign_ingresses(body: str, jd_from: float, jd_to: float,
                        step_days: float = 0.5) -> list[dict]:
    """
    Crossings of a 30 degree sign boundary in [jd_from, jd_to], in either
    direction. Retrograde bodies genuinely re-cross boundaries, so both
    forward and backward crossings are reported and tagged.
    Returns [{"jd", "sign_index", "direction"}], sign_index 0 = Aries.
    """
    swe.set_ephe_path(_EPHE_PATH)
    pid = _PLANET_IDS[body]

    out = []
    prev_jd = jd_from
    prev_lon = _body_lon(pid, prev_jd)
    jd = jd_from + step_days
    while jd <= jd_to:
        lon = _body_lon(pid, jd)
        prev_sign, sign = int(prev_lon // 30), int(lon // 30)
        if prev_sign != sign:
            # Wrapping 359 -> 001 is forward motion, not a 11-sign jump back.
            forward = ((lon - prev_lon) % 360) < 180
            boundary = (sign * 30.0) if forward else (prev_sign * 30.0)
            lo, hi = prev_jd, jd
            for _ in range(60):
                mid = (lo + hi) / 2
                if int(_body_lon(pid, mid) // 30) == prev_sign:
                    lo = mid
                else:
                    hi = mid
            out.append({
                "jd": (lo + hi) / 2,
                "sign_index": sign,
                "direction": "direct" if forward else "retrograde",
                "boundary": boundary,
            })
        prev_jd, prev_lon = jd, lon
        jd += step_days
    return out


def find_eclipses(jd_from: float, jd_to: float) -> list[dict]:
    """
    Solar and lunar eclipses with maximum falling in [jd_from, jd_to].
    Returns [{"jd", "body", "kind", "longitude"}]. `body` is "sun" or "moon",
    naming the luminary being eclipsed, and `longitude` is that luminary's.
    """
    swe.set_ephe_path(_EPHE_PATH)
    out = []

    for body, finder in (("sun", swe.sol_eclipse_when_glob),
                         ("moon", swe.lun_eclipse_when)):
        jd = jd_from
        # Eclipses come in seasons roughly six months apart, never more than
        # a handful in an eight month window. The cap is a runaway guard.
        for _ in range(40):
            retflag, tret = finder(jd, _FLAGS, 0, False)
            peak = tret[0]
            if peak > jd_to:
                break
            kind = next((label for bit, label in ECLIPSE_KINDS.items()
                         if retflag & bit), "unknown")
            out.append({
                "jd": peak,
                "body": body,
                "kind": kind,
                "longitude": _body_lon(_PLANET_IDS[body], peak),
            })
            jd = peak + 1.0

    out.sort(key=lambda e: e["jd"])
    return out


# ---------------------------------------------------------------------------
# Sunrise and sunset, for planetary hours.
#
# Electional work divides the day into 12 unequal hours from sunrise to sunset
# and 12 more from sunset to sunrise, and rules each by a planet in Chaldean
# order. That needs real rise and set times for a place, not clock noon.
# ---------------------------------------------------------------------------
def sun_rise_set(year: int, month: int, day: int,
                 lat: float, lon: float) -> tuple[float, float]:
    """
    (sunrise_jd, sunset_jd) for the civil day at lat/lon. lon east positive.
    Raises if the Sun neither rises nor sets, which happens above the polar
    circles and would otherwise return a silently meaningless hour.
    """
    swe.set_ephe_path(_EPHE_PATH)
    jd0 = swe.julday(year, month, day, 0.0)
    geo = (lon, lat, 0.0)
    ok_r, tret_r = swe.rise_trans(jd0, swe.SUN, swe.CALC_RISE, geo)
    ok_s, tret_s = swe.rise_trans(jd0, swe.SUN, swe.CALC_SET, geo)
    if ok_r < 0 or ok_s < 0:
        raise ValueError(f"Sun does not rise and set on {year}-{month}-{day} "
                         f"at {lat}, {lon}")
    return tret_r[0], tret_s[0]
