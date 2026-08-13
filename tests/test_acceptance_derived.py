"""
Acceptance tests — derived chart layers (addendum Part 2).
Progressions, solar/lunar returns, profections, connection chart,
synastry, composite, transits.
Reference chart: the primary reference birth moment (see test_acceptance_astrology) —
Barack Obama, 4 Aug 1961 19:24 AHST (= 5 Aug 05:24 UT), Honolulu.

Assertion tiers, following the convention in test_fixtures.py:
  "expect" — independently checkable (exactness maths, house arithmetic, or
             an externally published value).
  "pin"    — engine-derived regression pins that guard against silent drift
             but are not externally verified.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date

from src.ephemeris_core import calc_chart, calc_at_jd, julian_day, jd_to_datetime_tuple
from src.astrology import longitude_to_sign_degree
from src.derived_charts import (
    progressed_positions,
    solar_return,
    lunar_return,
    annual_profection,
    completed_age,
    synastry_aspects,
    composite_positions,
    circular_midpoint,
    transit_aspects_to_natal,
)
from src.human_design import compute_hd_chart
from src.hd_connection import connection_chart, hd_transit_overlay

BIRTH = dict(year=1961, month=8, day=5, hour_ut=5 + 24/60,
             lat=21.3069, lon=-157.8583)
BIRTH_DATE = date(1961, 8, 4)          # local birth date (Honolulu)
BIRTH_JD = julian_day(1961, 8, 5, 5 + 24/60)

_natal = calc_chart(**BIRTH)
_natal_positions = {name: {"longitude": p.longitude, "speed": p.speed,
                           "retrograde": p.retrograde}
                    for name, p in _natal.planets.items()}


# ---------------------------------------------------------------------------
# 2. Secondary progressions  [pin]
# The day-for-a-year arithmetic is independently checkable; the resulting
# positions below are engine-derived regression pins for this chart.
# ---------------------------------------------------------------------------
def test_progressed_moon():
    target_jd = julian_day(2026, 7, 19, 12)
    prog = progressed_positions(BIRTH_JD, target_jd)
    sign, deg = longitude_to_sign_degree(prog["positions"]["moon"]["longitude"])
    assert sign == "Libra", f"progressed Moon sign {sign} ≠ Libra"
    assert 8 <= deg <= 9.5, f"progressed Moon {deg:.2f}° not ~8°46′ Libra"


def test_progressed_elapsed_years():
    """The day-for-a-year rule itself: elapsed years must equal the age in
    tropical years, and the progressed JD must be birth_jd + that many days."""
    target_jd = julian_day(2026, 7, 19, 12)
    prog = progressed_positions(BIRTH_JD, target_jd)
    expected_years = (target_jd - BIRTH_JD) / 365.24219
    assert abs(prog["elapsed_years"] - expected_years) < 1e-9
    assert abs(prog["progressed_jd"] - (BIRTH_JD + expected_years)) < 1e-9
    assert 64 < prog["elapsed_years"] < 65, "should be ~64.96 years"


# ---------------------------------------------------------------------------
# 3. Solar return
# ---------------------------------------------------------------------------
def test_solar_return_exactness():
    natal_sun = _natal.planets["sun"].longitude
    return_jd, chart = solar_return(natal_sun, 2026, BIRTH["lat"], BIRTH["lon"],
                                    birth_month=8, birth_day=4)
    diff = abs(chart.planets["sun"].longitude - natal_sun)
    diff = min(diff, 360 - diff)
    assert diff < 1/60, f"SR Sun off natal by {diff*60:.3f}′ (must be <1′)"

    y, m, d, h = jd_to_datetime_tuple(return_jd)
    assert (m, d) in {(8, 3), (8, 4), (8, 5), (8, 6)}, (
        f"SR date {y}-{m:02d}-{d:02d} not within a day of the birthday"
    )


# ---------------------------------------------------------------------------
# 4. Lunar return
# ---------------------------------------------------------------------------
def test_lunar_return_exactness():
    natal_moon = _natal.planets["moon"].longitude
    from_jd = julian_day(2026, 7, 1, 0)
    return_jd, chart = lunar_return(natal_moon, from_jd, BIRTH["lat"], BIRTH["lon"])
    diff = abs(chart.planets["moon"].longitude - natal_moon)
    diff = min(diff, 360 - diff)
    assert diff < 1/60, f"LR Moon off natal by {diff*60:.3f}′ (must be <1′)"
    assert from_jd < return_jd < from_jd + 29, "LR not within one lunar cycle"


# ---------------------------------------------------------------------------
# 5. Annual profections (Aquarius rising) — pure house arithmetic, so these
#    are checkable by hand rather than needing an external source.
# ---------------------------------------------------------------------------
def test_profection_age_64():
    # age 64 → (64%12)+1 = 5th house from Aquarius = Gemini → Mercury
    prof = annual_profection(_natal.ascendant, BIRTH_DATE, date(2026, 7, 19))
    assert prof["age"] == 64, f"age {prof['age']} ≠ 64"
    assert prof["profected_house"] == 5
    assert prof["profected_sign"] == "Gemini"
    assert prof["lord_of_year"] == "Mercury"


def test_profection_age_66():
    # age 66 → (66%12)+1 = 7th house from Aquarius = Leo → Sun
    prof = annual_profection(_natal.ascendant, BIRTH_DATE, date(2028, 7, 19))
    assert prof["age"] == 66
    assert prof["profected_house"] == 7
    assert prof["profected_sign"] == "Leo"
    assert prof["lord_of_year"] == "Sun"


def test_completed_age_boundary():
    assert completed_age(BIRTH_DATE, date(2026, 8, 3)) == 64
    assert completed_age(BIRTH_DATE, date(2026, 8, 4)) == 65


# ---------------------------------------------------------------------------
# 6. Connection chart (HD)
# ---------------------------------------------------------------------------
_hd = compute_hd_chart(**BIRTH)


def test_connection_self_reproduces_solo():
    conn = connection_chart(_hd, _hd)
    assert set(conn["defined_centers"]) == _hd.defined_centers, (
        f"self-connection centers {conn['defined_centers']} ≠ solo "
        f"{sorted(_hd.defined_centers)}"
    )
    # Every self-channel must be companionship; nothing electromagnetic
    assert conn["electromagnetic"] == [], "self-connection cannot be electromagnetic"
    assert set(map(tuple, conn["companionship"])) == _hd.defined_channels
    assert conn["newly_defined_centers"] == []


def test_connection_cross_completion():
    # Second person: 2001-03-08 19:30 UTC Toronto (validated live earlier —
    # gates include 20 and 57 among others)
    other = compute_hd_chart(2001, 3, 8, 19.5, 43.6532, -79.3832)
    conn = connection_chart(_hd, other)
    # The composite may only contain channels whose two gates exist in the union
    union = _hd.all_gates | other.all_gates
    for ch in conn["channels"]:
        a, b = ch["channel"]
        assert a in union and b in union
    # Any channel neither person has alone must be electromagnetic or absent
    for a, b in conn["electromagnetic"]:
        a_full = a in _hd.all_gates and b in _hd.all_gates
        b_full = a in other.all_gates and b in other.all_gates
        assert not a_full and not b_full, (
            f"channel {a}-{b} marked electromagnetic but someone has it fully"
        )


# ---------------------------------------------------------------------------
# 7. Synastry + composite
# ---------------------------------------------------------------------------
def test_synastry_symmetric():
    other_chart = calc_chart(2001, 3, 8, 19.5, 43.6532, -79.3832)
    other_positions = {name: {"longitude": p.longitude}
                       for name, p in other_chart.planets.items()}
    ab = synastry_aspects(_natal_positions, other_positions)
    ba = synastry_aspects(other_positions, _natal_positions)
    ab_set = {(x["a"], x["b"], x["aspect"]) for x in ab}
    ba_set = {(x["b"], x["a"], x["aspect"]) for x in ba}
    assert ab_set == ba_set, "synastry grid must be symmetric in aspect type"


def test_composite_sun_is_midpoint():
    other_chart = calc_chart(2001, 3, 8, 19.5, 43.6532, -79.3832)
    other_positions = {name: {"longitude": p.longitude}
                       for name, p in other_chart.planets.items()}
    comp = composite_positions(_natal_positions, other_positions)
    expected = circular_midpoint(_natal_positions["sun"]["longitude"],
                                 other_positions["sun"]["longitude"])
    assert abs(comp["sun"]["longitude"] - expected) < 1e-9


def test_circular_midpoint_wrap():
    # 350° and 10° → short-arc midpoint is 0°, not 180°
    assert abs(circular_midpoint(350, 10) - 0) < 1e-9
    assert abs(circular_midpoint(10, 350) - 0) < 1e-9
    assert abs(circular_midpoint(0, 180) - 90) < 1e-9  # tie: either 90 or 270; take arc from a


# ---------------------------------------------------------------------------
# 8. Transits
# March equinox 2026 (almanac: 2026-03-20 ≈ 14:46 UTC) — Sun at exactly 0° Aries.
# ---------------------------------------------------------------------------
def test_transit_sun_vs_almanac():
    jd = julian_day(2026, 3, 20, 14 + 46/60)
    sun_lon = calc_at_jd(jd)["sun"]["longitude"]
    # distance from 0° Aries, wrap-safe
    diff = min(sun_lon, 360 - sun_lon)
    assert diff < 2/60, f"Sun at equinox {diff*60:.2f}′ from 0° Aries (must be <2′)"


def test_transit_aspects_shape():
    jd = julian_day(2026, 7, 19, 12)
    result = transit_aspects_to_natal(_natal_positions, jd)
    assert "transiting" in result and "aspects" in result
    assert len(result["transiting"]) == 13
    for a in result["aspects"]:
        assert a["a"].startswith("t_")


def test_hd_transit_overlay_consistency():
    jd = julian_day(2026, 7, 19, 12)
    overlay = hd_transit_overlay(_hd, jd)
    # natal channels are always a subset of all active channels
    assert _hd.defined_channels <= set(map(tuple, overlay["all_active_channels"]))
    # new channels must not include any natal channel
    assert not (set(map(tuple, overlay["new_channels"])) & _hd.defined_channels)
    assert 1 <= len(overlay["transit_gates"]) <= 26


if __name__ == "__main__":
    import traceback

    tests = [
        test_progressed_moon,
        test_progressed_elapsed_years,
        test_solar_return_exactness,
        test_lunar_return_exactness,
        test_profection_age_64,
        test_profection_age_66,
        test_completed_age_boundary,
        test_connection_self_reproduces_solo,
        test_connection_cross_completion,
        test_synastry_symmetric,
        test_composite_sun_is_midpoint,
        test_circular_midpoint_wrap,
        test_transit_sun_vs_almanac,
        test_transit_aspects_shape,
        test_hd_transit_overlay_consistency,
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
