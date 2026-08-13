"""
Acceptance test — astrology layer.
Input: 1994-10-16, 09:57 EDT (= 13:57 UTC), Kingston, Ontario (44.2333°N, 76.5°W)
All positions must match the known-correct reference to within ±1°.
Exact values (to the arcminute) are asserted for Ascendant, MC, and Juno.
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
# Known-correct reference chart
# -------------------------------------------------------------------------
BIRTH = dict(year=1994, month=10, day=16, hour_ut=13 + 57/60,
             lat=44.2333, lon=-76.5)

EXPECTED_PLANETS = {
    # name: (sign, approx_degree_in_sign, whole_sign_house)
    "sun":       ("Libra",       22, 12),
    "moon":      ("Pisces",      20,  5),
    "mercury":   ("Scorpio",      2,  1),
    "venus":     ("Scorpio",     17,  1),
    "mars":      ("Leo",          6, 10),
    "jupiter":   ("Scorpio",     18,  1),
    "saturn":    ("Pisces",       6,  5),
    "uranus":    ("Capricorn",   22,  3),
    "neptune":   ("Capricorn",   20,  3),
    "pluto":     ("Scorpio",     26,  1),
    "true_node": ("Scorpio",     14,  1),
    "chiron":    ("Virgo",       20, 11),
    "juno":      ("Scorpio",     14,  1),  # 14°57′
}

# Exact positions (verified to the arcminute)
EXPECTED_ASC_LON = 231.449  # 21°27′ Scorpio
EXPECTED_MC_LON  = 155.816  # 5°49′ Virgo
EXPECTED_JUNO_LON = 224.953 # 14°57′ Scorpio


def get_chart():
    return calc_chart(**BIRTH)


def test_ascendant_exact():
    chart = get_chart()
    assert abs(chart.ascendant - EXPECTED_ASC_LON) < 0.01, (
        f"Asc {chart.ascendant:.3f}° ≠ expected {EXPECTED_ASC_LON}°"
    )


def test_mc_exact():
    chart = get_chart()
    assert abs(chart.mc - EXPECTED_MC_LON) < 0.01, (
        f"MC {chart.mc:.3f}° ≠ expected {EXPECTED_MC_LON}°"
    )


def test_ascendant_sign():
    chart = get_chart()
    sign, deg = longitude_to_sign_degree(chart.ascendant)
    assert sign == "Scorpio", f"Asc sign {sign} ≠ Scorpio"
    assert 21 <= deg < 22, f"Asc degree {deg:.3f}° not in 21°xx′ range"


def test_mc_sign():
    chart = get_chart()
    sign, deg = longitude_to_sign_degree(chart.mc)
    assert sign == "Virgo", f"MC sign {sign} ≠ Virgo"
    assert 5 <= deg < 6, f"MC degree {deg:.3f}° not in 5°xx′ range"


def test_juno_exact():
    chart = get_chart()
    assert abs(chart.planets["juno"].longitude - EXPECTED_JUNO_LON) < 0.01, (
        f"Juno {chart.planets['juno'].longitude:.3f}° ≠ {EXPECTED_JUNO_LON}°"
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


def test_mercury_retrograde():
    chart = get_chart()
    assert chart.planets["mercury"].retrograde, "Mercury should be retrograde"


def test_format_output_smoke():
    chart = get_chart()
    out = format_natal_chart(chart)
    assert "planets" in out
    assert "ascendant" in out
    assert "aspects" in out
    # Spot-check a few display strings
    assert "Libra" in out["planets"]["sun"]["display"]
    assert "Scorpio" in out["ascendant"]["display"]


if __name__ == "__main__":
    import traceback, sys

    tests = [
        test_ascendant_exact, test_mc_exact,
        test_ascendant_sign, test_mc_sign,
        test_juno_exact, test_planet_signs_and_houses,
        test_mercury_retrograde, test_format_output_smoke,
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
