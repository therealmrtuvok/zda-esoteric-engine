"""
astrology layer — consumes ephemeris_core, never imports swisseph.
Produces: signs, houses (Whole Sign + Placidus), aspects.
"""

from .ephemeris_core import ChartData, Planet

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

# Aspect definitions: (name, exact angle, orb)
ASPECTS = [
    ("Conjunction",   0,   8),
    ("Opposition",  180,   8),
    ("Trine",       120,   8),
    ("Square",       90,   7),
    ("Sextile",      60,   6),
    ("Quincunx",    150,   3),
    ("Semi-sextile",  30,   2),
]

ASPECT_SYMBOLS = {
    "Conjunction":   "☌",
    "Opposition":    "☍",
    "Trine":         "△",
    "Square":        "□",
    "Sextile":       "⚹",
    "Quincunx":      "⚻",
    "Semi-sextile":  "⚺",
}


def longitude_to_sign_degree(lon: float) -> tuple[str, float]:
    """Return (sign_name, degree_within_sign) for an ecliptic longitude."""
    lon = lon % 360
    sign_idx = int(lon / 30)
    return SIGNS[sign_idx], lon % 30


def dms(degree_fraction: float) -> str:
    """Convert decimal degrees to D°M'S″ string."""
    d = int(degree_fraction)
    m = int((degree_fraction - d) * 60)
    s = round(((degree_fraction - d) * 60 - m) * 60)
    return f"{d}°{m:02d}′{s:02d}″"


def planet_sign_str(lon: float, retrograde: bool = False) -> str:
    sign, deg = longitude_to_sign_degree(lon)
    r = " ℞" if retrograde else ""
    return f"{dms(deg)} {sign}{r}"


def whole_sign_house(planet_lon: float, asc_lon: float) -> int:
    """Return 1–12 Whole Sign house number."""
    asc_sign = int(asc_lon / 30)
    planet_sign = int(planet_lon % 360 / 30)
    return (planet_sign - asc_sign) % 12 + 1


def placidus_house(planet_lon: float, cusps: list[float]) -> int:
    """Return 1–12 Placidus house number given 12 cusp longitudes."""
    lon = planet_lon % 360
    for h in range(12):
        cusp_start = cusps[h] % 360
        cusp_end = cusps[0] % 360 if h == 11 else cusps[h + 1] % 360
        if cusp_end < cusp_start:
            if lon >= cusp_start or lon < cusp_end:
                return h + 1
        else:
            if cusp_start <= lon < cusp_end:
                return h + 1
    return 1


def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def get_aspects(chart: ChartData, planets_a: list[str] = None,
                planets_b: list[str] = None) -> list[dict]:
    """
    Return list of aspect dicts between planets_a and planets_b.
    If either list is None, defaults to all planets.
    """
    all_names = list(chart.planets.keys())
    pa = planets_a or all_names
    pb = planets_b or all_names

    seen = set()
    results = []
    for a in pa:
        for b in pb:
            key = tuple(sorted((a, b)))
            if a == b or key in seen:
                continue
            seen.add(key)
            lon_a = chart.planets[a].longitude
            lon_b = chart.planets[b].longitude
            diff = _angular_distance(lon_a, lon_b)
            for asp_name, exact, orb in ASPECTS:
                if abs(diff - exact) <= orb:
                    results.append({
                        "planet_a": a,
                        "planet_b": b,
                        "aspect": asp_name,
                        "symbol": ASPECT_SYMBOLS[asp_name],
                        "orb": round(abs(diff - exact), 2),
                        "applying": chart.planets[a].speed > chart.planets[b].speed,
                    })
                    break
    return results


def format_natal_chart(chart: ChartData) -> dict:
    """Return a clean JSON-serialisable natal chart dict."""
    asc = chart.ascendant
    asc_sign, asc_deg = longitude_to_sign_degree(asc)
    mc_sign, mc_deg = longitude_to_sign_degree(chart.mc)

    planet_rows = {}
    for name, p in chart.planets.items():
        sign, deg = longitude_to_sign_degree(p.longitude)
        ws_house = whole_sign_house(p.longitude, asc)
        pl_house = placidus_house(p.longitude, chart.houses_placidus)
        planet_rows[name] = {
            "longitude": round(p.longitude, 4),
            "sign": sign,
            "degree_in_sign": round(deg, 4),
            "display": planet_sign_str(p.longitude, p.retrograde),
            "retrograde": p.retrograde,
            "house_whole_sign": ws_house,
            "house_placidus": pl_house,
            "speed": round(p.speed, 6),
        }

    return {
        "ascendant": {
            "longitude": round(asc, 4),
            "sign": asc_sign,
            "degree_in_sign": round(asc_deg, 4),
            "display": dms(asc_deg) + " " + asc_sign,
        },
        "mc": {
            "longitude": round(chart.mc, 4),
            "sign": mc_sign,
            "degree_in_sign": round(mc_deg, 4),
            "display": dms(mc_deg) + " " + mc_sign,
        },
        "planets": planet_rows,
        "aspects": get_aspects(chart),
        "houses_whole_sign": [round(c, 4) for c in chart.houses_whole_sign],
        "houses_placidus": [round(c, 4) for c in chart.houses_placidus],
    }
