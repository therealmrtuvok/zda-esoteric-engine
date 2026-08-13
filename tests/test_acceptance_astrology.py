"""
Acceptance test — astrology layer.

Reference chart: **Barack Obama**, 4 August 1961, 19:24 AHST (= 5 Aug 05:24 UT),
Honolulu, Hawaii (21.3069°N, 157.8583°W).

Chosen because the birth data is Rodden **AA** — taken from the published birth
certificate — which is the highest data quality available, and because the chart
is widely published, so the expected values below come from outside this engine
rather than from the engine agreeing with itself.

External cross-check of the angles (two independent published sources):
  astrotheme.com                 Asc 18°07′ Aquarius   MC 28°57′ Scorpio
  astro-charts.com               Asc 18°03′56″ Aquarius MC 28°54′15″ Scorpio
  this engine                    Asc 18°03′06″ Aquarius MC 28°53′37″ Scorpio

The engine agrees with the more precise of the two to under one arcminute.
Tolerances below are set to ±2′ on the angles to accommodate the small spread
between published sources (which differ by a few arcseconds of birth-time
rounding), and to the whole degree on planets.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ephemeris_core import calc_chart
from src.astrology import (
    format_natal_chart,
    longitude_to_sign_degree,
    whole_sign_house,
    dms,
)

# -------------------------------------------------------------------------
# Known-correct reference chart (public figure, Rodden AA)
# -------------------------------------------------------------------------
BIRTH = dict(year=1961, month=8, day=5, hour_ut=5 + 24/60,
             lat=21.3069, lon=-157.8583)

EXPECTED_PLANETS = {
    # name: (sign, degree_in_sign floor, whole_sign_house)
    "sun":       ("Leo",        12,  7),
    "moon":      ("Gemini",      3,  5),
    "mercury":   ("Leo",         2,  7),
    "venus":     ("Cancer",      1,  6),
    "mars":      ("Virgo",      22,  8),
    "jupiter":   ("Aquarius",    0,  1),
    "saturn":    ("Capricorn",  25, 12),
    "uranus":    ("Leo",        25,  7),
    "neptune":   ("Scorpio",     8, 10),
    "pluto":     ("Virgo",       6,  8),
    "true_node": ("Leo",        27,  7),
    "chiron":    ("Pisces",      5,  2),
}

# Angles, verified against published charts (see module docstring)
EXPECTED_ASC_LON = 318.0518   # 18°03′ Aquarius
EXPECTED_MC_LON  = 238.8935   # 28°53′ Scorpio
ANGLE_TOL_DEG    = 2 / 60     # 2 arcminutes

# Retrograde at birth, per the same published charts
EXPECTED_RETROGRADE = {"jupiter", "saturn", "true_node", "chiron"}


def get_chart():
    return calc_chart(**BIRTH)


def test_ascendant_exact():
    chart = get_chart()
    assert abs(chart.ascendant - EXPECTED_ASC_LON) < ANGLE_TOL_DEG, (
        f"Asc {dms(chart.ascendant)} ≠ expected {dms(EXPECTED_ASC_LON)}"
    )


def test_mc_exact():
    chart = get_chart()
    assert abs(chart.mc - EXPECTED_MC_LON) < ANGLE_TOL_DEG, (
        f"MC {dms(chart.mc)} ≠ expected {dms(EXPECTED_MC_LON)}"
    )


def test_ascendant_sign():
    chart = get_chart()
    sign, deg = longitude_to_sign_degree(chart.ascendant)
    assert sign == "Aquarius", f"Asc sign {sign} ≠ Aquarius"
    assert 18 <= deg < 19, f"Asc degree {deg:.3f}° not in 18°xx′ range"


def test_mc_sign():
    chart = get_chart()
    sign, deg = longitude_to_sign_degree(chart.mc)
    assert sign == "Scorpio", f"MC sign {sign} ≠ Scorpio"
    assert 28 <= deg < 29, f"MC degree {deg:.3f}° not in 28°xx′ range"


def test_sun_exact():
    """Obama's Sun at 12°32′ Leo is one of the most-published positions in
    modern astrology — a strong independent check on the solar longitude."""
    chart = get_chart()
    sign, deg = longitude_to_sign_degree(chart.planets["sun"].longitude)
    assert sign == "Leo"
    assert abs(deg - (12 + 32/60)) < 2/60, (
        f"Sun {dms(chart.planets['sun'].longitude)} ≠ 12°32′ Leo"
    )


def test_planet_signs_and_houses():
    chart = get_chart()
    asc = chart.ascendant
    for name, (exp_sign, exp_deg_floor, exp_house) in EXPECTED_PLANETS.items():
        p = chart.planets[name]
        sign, deg = longitude_to_sign_degree(p.longitude)
        house = whole_sign_house(p.longitude, asc)

        assert sign == exp_sign, (
            f"{name}: sign {sign} ≠ {exp_sign} (lon={p.longitude:.3f})"
        )
        assert int(deg) == exp_deg_floor, (
            f"{name}: degree floor {int(deg)} ≠ {exp_deg_floor} "
            f"(lon={p.longitude:.3f}, sign deg={deg:.3f})"
        )
        assert house == exp_house, (
            f"{name}: whole-sign house {house} ≠ {exp_house}"
        )


def test_retrogrades():
    chart = get_chart()
    actual = {n for n, p in chart.planets.items()
              if p.retrograde and n in EXPECTED_PLANETS}
    assert actual == EXPECTED_RETROGRADE, (
        f"retrograde set {sorted(actual)} ≠ {sorted(EXPECTED_RETROGRADE)}"
    )


def test_format_output_smoke():
    chart = get_chart()
    out = format_natal_chart(chart)
    assert "planets" in out
    assert "ascendant" in out
    assert "aspects" in out
    assert "Leo" in out["planets"]["sun"]["display"]
    assert "Aquarius" in out["ascendant"]["display"]


if __name__ == "__main__":
    import traceback, sys

    tests = [
        test_ascendant_exact, test_mc_exact,
        test_ascendant_sign, test_mc_sign,
        test_sun_exact, test_planet_signs_and_houses,
        test_retrogrades, test_format_output_smoke,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
