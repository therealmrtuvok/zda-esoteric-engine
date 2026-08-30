"""
Sky events: the astrology layer of the energy calendar.

Turns the raw instants from ephemeris_core into dated, labelled events for a
range: retrograde stations, lunations, eclipses, sign ingresses, and transiting
aspects to a natal chart with their in-orb windows.

Nothing here imports swisseph. Nothing here decides what an event means either,
that belongs in the meaning tables.

On orbs: the natal ASPECTS table in astrology.py uses orbs up to 8 degrees,
which is right for reading a birth chart and wrong for a calendar. Pluto holds
an 8 degree square for years. Transit windows here default to 1.5 degrees, so a
window is weeks rather than seasons, and every exact pass inside it is dated
separately because a retrograde can make the same aspect exact three times.
"""

from .ephemeris_core import (
    calc_at_jd, jd_to_datetime_tuple, julian_day,
    find_stations, find_lunations, find_sign_ingresses, find_eclipses,
)
from .astrology import ASPECT_SYMBOLS

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Bodies whose stations and ingresses are worth a calendar entry. The Sun and
# Moon are excluded because they never station; the Moon's ingresses are
# excluded because it changes sign every two and a half days, which is noise.
STATION_BODIES = ["mercury", "venus", "mars", "jupiter", "saturn",
                  "uranus", "neptune", "pluto", "chiron"]

# Slow enough that a sign change is a genuine chapter marker.
INGRESS_BODIES = ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto",
                  "true_node", "chiron"]

# Transiting bodies that carry a real arc. Faster bodies are handled by the
# Human Design layer, which is already tracking them gate by gate.
TRANSIT_BODIES = ["jupiter", "saturn", "uranus", "neptune", "pluto", "chiron"]

# Natal points worth being hit. Angles are included only when a birth time is
# known, which the caller signals by passing them in.
NATAL_POINTS = ["sun", "moon", "mercury", "venus", "mars", "jupiter",
                "saturn", "uranus", "neptune", "pluto", "true_node", "chiron"]

# Tighter than the natal set, and hard aspects only by default: those are the
# ones that describe something happening rather than something available.
TRANSIT_ASPECTS = [
    ("Conjunction", 0.0),
    ("Opposition", 180.0),
    ("Square", 90.0),
    ("Trine", 120.0),
    ("Sextile", 60.0),
]


def iso(jd: float) -> str:
    y, m, d, _h = jd_to_datetime_tuple(jd)
    return f"{y:04d}-{m:02d}-{d:02d}"


def iso_time(jd: float) -> str:
    y, m, d, h = jd_to_datetime_tuple(jd)
    return f"{y:04d}-{m:02d}-{d:02d}T{int(h):02d}:{int(h % 1 * 60):02d}Z"


def sign_of(lon: float) -> str:
    return SIGNS[int(lon // 30) % 12]


def degree_in_sign(lon: float) -> float:
    return lon % 30


def _aspect_orb(a: float, b: float, exact_angle: float) -> float:
    """Signed distance from exact, taking whichever side of the axis is nearer."""
    d = (a - b) % 360
    best = None
    for candidate in (exact_angle, (360 - exact_angle) % 360):
        diff = (d - candidate + 180) % 360 - 180
        if best is None or abs(diff) < abs(best):
            best = diff
    return best


# ---------------------------------------------------------------------------
# Standalone sky events, independent of any birth chart
# ---------------------------------------------------------------------------
def mundane_events(jd_start: float, jd_end: float) -> list[dict]:
    """
    Everything happening in the sky itself over the range, with no reference to
    a natal chart: stations, lunations, eclipses, ingresses.
    Returns a flat date-sorted list of event dicts, each with `kind`.
    """
    events: list[dict] = []

    for body in STATION_BODIES:
        for st in find_stations(body, jd_start, jd_end):
            events.append({
                "kind": "station",
                "jd": st["jd"],
                "date": iso(st["jd"]),
                "body": body,
                "direction": st["direction"],
                "sign": sign_of(st["longitude"]),
                "degree": round(degree_in_sign(st["longitude"]), 2),
            })

    eclipses = find_eclipses(jd_start, jd_end)
    eclipse_days = {iso(e["jd"]) for e in eclipses}
    for ec in eclipses:
        events.append({
            "kind": "eclipse",
            "jd": ec["jd"],
            "date": iso(ec["jd"]),
            "body": ec["body"],
            "eclipse_kind": ec["kind"],
            "sign": sign_of(ec["longitude"]),
            "degree": round(degree_in_sign(ec["longitude"]), 2),
        })

    for lu in find_lunations(jd_start, jd_end):
        # A lunation that is also an eclipse is reported once, as the eclipse.
        if iso(lu["jd"]) in eclipse_days:
            continue
        events.append({
            "kind": "lunation",
            "jd": lu["jd"],
            "date": iso(lu["jd"]),
            "phase": lu["phase"],
            "sign": sign_of(lu["longitude"]),
            "degree": round(degree_in_sign(lu["longitude"]), 2),
        })

    for body in INGRESS_BODIES:
        for ing in find_sign_ingresses(body, jd_start, jd_end):
            events.append({
                "kind": "ingress",
                "jd": ing["jd"],
                "date": iso(ing["jd"]),
                "body": body,
                "sign": SIGNS[ing["sign_index"] % 12],
                "direction": ing["direction"],
            })

    events.sort(key=lambda e: e["jd"])
    return events


# ---------------------------------------------------------------------------
# Transiting aspects to a natal chart, with windows
# ---------------------------------------------------------------------------
def scan_aspect_windows(natal_points: dict, jd_start: float, jd_end: float,
                        transit_bodies: list[str] = None,
                        aspects: list[tuple] = None,
                        orb: float = 1.5,
                        step_days: float = 1.0) -> list[dict]:
    """
    Windows where a transiting body holds an aspect to a natal point inside
    `orb`, with every exact pass inside the window dated separately.

    natal_points: {name: longitude} for the natal chart. Angles ("ascendant",
    "midheaven") can be included and are treated like any other point.

    Returns [{transit_body, natal_point, aspect, start, end, exact: [dates],
              passes, ongoing_at_start, ongoing_at_end}]

    A window that is already open at jd_start, or still open at jd_end, is
    flagged rather than silently truncated: a Pluto conjunction that has been
    in orb for a year is a different fact from one that just began.
    """
    transit_bodies = transit_bodies or TRANSIT_BODIES
    aspects = aspects or TRANSIT_ASPECTS

    # Precompute the whole ephemeris walk once rather than per pair.
    samples: list[tuple[float, dict]] = []
    jd = jd_start
    while jd <= jd_end + 1e-9:
        samples.append((jd, calc_at_jd(jd)))
        jd += step_days

    windows = []
    for body in transit_bodies:
        for point, natal_lon in natal_points.items():
            for asp_name, exact_angle in aspects:
                open_w = None
                prev_orb = None
                for i, (s_jd, pos) in enumerate(samples):
                    if body not in pos:
                        continue
                    o = _aspect_orb(pos[body]["longitude"], natal_lon, exact_angle)
                    in_orb = abs(o) <= orb

                    if in_orb and open_w is None:
                        open_w = {
                            "transit_body": body,
                            "natal_point": point,
                            "aspect": asp_name,
                            "symbol": ASPECT_SYMBOLS[asp_name],
                            "start": iso(s_jd),
                            "exact": [],
                            "ongoing_at_start": i == 0,
                        }
                    if open_w is not None and prev_orb is not None and in_orb:
                        # Sign change in the signed orb means it went exact
                        # between the two samples. Bisect for the day.
                        if (prev_orb < 0) != (o < 0) and abs(prev_orb - o) < 90:
                            lo_jd, hi_jd = samples[i - 1][0], s_jd
                            for _ in range(30):
                                mid = (lo_jd + hi_jd) / 2
                                m = _aspect_orb(
                                    calc_at_jd(mid)[body]["longitude"],
                                    natal_lon, exact_angle)
                                if (m < 0) == (prev_orb < 0):
                                    lo_jd = mid
                                else:
                                    hi_jd = mid
                            open_w["exact"].append(iso((lo_jd + hi_jd) / 2))
                    if not in_orb and open_w is not None:
                        open_w["end"] = iso(samples[i - 1][0])
                        open_w["ongoing_at_end"] = False
                        open_w["passes"] = len(open_w["exact"])
                        windows.append(open_w)
                        open_w = None
                    prev_orb = o

                if open_w is not None:
                    open_w["end"] = iso(samples[-1][0])
                    open_w["ongoing_at_end"] = True
                    open_w["passes"] = len(open_w["exact"])
                    windows.append(open_w)

    windows.sort(key=lambda w: (w["start"], w["transit_body"]))
    return windows


def natal_points_from_chart(chart, include_angles: bool = True) -> dict:
    """
    {name: longitude} for a ChartData, ready for scan_aspect_windows.
    Angles are only meaningful with an accurate birth time, so a caller
    working from a date-only birth should pass include_angles=False.
    """
    pts = {name: p.longitude for name, p in chart.planets.items()
           if name in NATAL_POINTS}
    if include_angles:
        pts["ascendant"] = chart.ascendant
        pts["midheaven"] = chart.mc
    return pts
