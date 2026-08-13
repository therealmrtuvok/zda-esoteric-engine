"""
Acceptance test — Human Design layer.

Same reference chart as the astrology test: Barack Obama, 4 Aug 1961
19:24 AHST (= 5 Aug 05:24 UT), Honolulu. Rodden AA birth data.

Expected Human Design values are published independently of this engine and
were cross-checked against two Human Design sources (see test_fixtures.py):
Projector / Emotional (Solar Plexus) / 6-2 / Single Definition / Left Angle,
with only the Root and Solar Plexus centres defined ("a single channel from
the Root to the Emotional System").

Every field must match before this layer is trusted.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import swisseph as swe
from src.human_design import compute_hd_chart
from src.hd_tables import longitude_to_activation, opposite_gate, GATE_WHEEL

BIRTH = dict(year=1961, month=8, day=5, hour_ut=5 + 24/60,
             lat=21.3069, lon=-157.8583)

# ---------------------------------------------------------------------------
# Known-correct HD reference (externally published; see module docstring)
# ---------------------------------------------------------------------------
EXPECTED = {
    "type":              "Projector",
    "profile":           "6/2",
    "authority":         "Emotional (Solar Plexus)",
    "definition":        "Single Definition",
    "incarnation_cross": "Left Angle Cross of Refinement (33/19 | 2/1)",
    "variable":          "PRL DRL",
    # Personality Sun gate/line
    "p_sun_gate":        33,
    "p_sun_line":         6,
    # Design Sun gate/line
    "d_sun_gate":         2,
    "d_sun_line":         2,
    # Only Root + Solar Plexus defined — the sourced description is
    # "one channel from the Root to the Emotional System" (channel 30-41)
    "defined_centers_count": 2,
    "undefined_center":  "Head",
    # Not-Self
    "not_self_theme":    "Bitterness",
    # Design date 1961-05-05 (JD ~2437424.7)
    "design_jd_approx":  2437425,
    "design_jd_tol":     3,           # ±3 days is generous
}


def get_chart():
    return compute_hd_chart(**BIRTH)


def test_personality_sun_gate_and_line():
    chart = get_chart()
    p_sun = chart.personality["sun"]
    assert p_sun.gate == EXPECTED["p_sun_gate"], (
        f"Personality Sun gate {p_sun.gate} ≠ {EXPECTED['p_sun_gate']}"
    )
    assert p_sun.line == EXPECTED["p_sun_line"], (
        f"Personality Sun line {p_sun.line} ≠ {EXPECTED['p_sun_line']}"
    )


def test_design_sun_gate_and_line():
    chart = get_chart()
    d_sun = chart.design["sun"]
    assert d_sun.gate == EXPECTED["d_sun_gate"], (
        f"Design Sun gate {d_sun.gate} ≠ {EXPECTED['d_sun_gate']}"
    )
    assert d_sun.line == EXPECTED["d_sun_line"], (
        f"Design Sun line {d_sun.line} ≠ {EXPECTED['d_sun_line']}"
    )


def test_earth_is_sun_opposite():
    chart = get_chart()
    p_sun_gate  = chart.personality["sun"].gate
    p_earth_gate = chart.personality["earth"].gate
    d_sun_gate  = chart.design["sun"].gate
    d_earth_gate = chart.design["earth"].gate

    assert opposite_gate(p_sun_gate) == p_earth_gate, (
        f"Personality Earth gate {p_earth_gate} ≠ opposite of {p_sun_gate} "
        f"({opposite_gate(p_sun_gate)})"
    )
    assert opposite_gate(d_sun_gate) == d_earth_gate, (
        f"Design Earth gate {d_earth_gate} ≠ opposite of {d_sun_gate} "
        f"({opposite_gate(d_sun_gate)})"
    )


def test_profile():
    chart = get_chart()
    assert chart.profile == EXPECTED["profile"], (
        f"Profile {chart.profile!r} ≠ {EXPECTED['profile']!r}"
    )


def test_type():
    chart = get_chart()
    assert chart.type_ == EXPECTED["type"], (
        f"Type {chart.type_!r} ≠ {EXPECTED['type']!r}"
    )


def test_authority():
    chart = get_chart()
    assert chart.authority == EXPECTED["authority"], (
        f"Authority {chart.authority!r} ≠ {EXPECTED['authority']!r}"
    )


def test_definition():
    chart = get_chart()
    assert chart.definition == EXPECTED["definition"], (
        f"Definition {chart.definition!r} ≠ {EXPECTED['definition']!r}"
    )


def test_defined_centers_count():
    chart = get_chart()
    n = len(chart.defined_centers)
    assert n == EXPECTED["defined_centers_count"], (
        f"Defined centers count {n} ≠ {EXPECTED['defined_centers_count']}\n"
        f"  Defined: {sorted(chart.defined_centers)}\n"
        f"  Undefined: {sorted(chart.undefined_centers)}"
    )


def test_head_undefined():
    chart = get_chart()
    assert EXPECTED["undefined_center"] in chart.undefined_centers, (
        f"Expected Head to be undefined; undefined = {chart.undefined_centers}"
    )


def test_incarnation_cross():
    chart = get_chart()
    assert chart.incarnation_cross == EXPECTED["incarnation_cross"], (
        f"Cross {chart.incarnation_cross!r}\n"
        f"  ≠ {EXPECTED['incarnation_cross']!r}"
    )


def test_variable():
    chart = get_chart()
    assert chart.variable == EXPECTED["variable"], (
        f"Variable {chart.variable!r} ≠ {EXPECTED['variable']!r}\n"
        f"  P Sun color={chart.personality['sun'].color}  "
        f"D Sun color={chart.design['sun'].color}  "
        f"P Node color={chart.personality['true_node'].color}  "
        f"D Node color={chart.design['true_node'].color}"
    )


def test_not_self_theme():
    chart = get_chart()
    assert chart.not_self_theme == EXPECTED["not_self_theme"], (
        f"Not-Self {chart.not_self_theme!r} ≠ {EXPECTED['not_self_theme']!r}"
    )


def test_design_date_approximate():
    chart = get_chart()
    diff = abs(chart.design_julian_day - EXPECTED["design_jd_approx"])
    assert diff <= EXPECTED["design_jd_tol"], (
        f"Design JD {chart.design_julian_day:.1f} off by {diff:.1f} days "
        f"from expected ~{EXPECTED['design_jd_approx']}"
    )


def test_gate_wheel_spot_checks():
    """
    Verify gate-wheel anchor positions independently of the HD chart.
    Gate 32 must start at 200.75° (index 46 from anchor 302°).
    Gate 62 must start at 110.75° (index 30).
    """
    assert GATE_WHEEL[46] == 32, f"GATE_WHEEL[46]={GATE_WHEEL[46]} ≠ 32"
    assert GATE_WHEEL[30] == 62, f"GATE_WHEEL[30]={GATE_WHEEL[30]} ≠ 62"
    assert opposite_gate(32) == 42, f"opposite(32)={opposite_gate(32)} ≠ 42"
    assert opposite_gate(62) == 61, f"opposite(62)={opposite_gate(62)} ≠ 61"


def test_all_gates_coverage():
    """All 64 integers 1–64 must appear exactly once in GATE_WHEEL."""
    assert sorted(GATE_WHEEL) == list(range(1, 65)), "GATE_WHEEL does not contain 1–64 exactly once"


def test_channel_inventory():
    """Exactly 36 channels; integration circuit fully present; every gate in ≥1 channel."""
    from src.hd_tables import CHANNELS
    assert len(CHANNELS) == 36, f"{len(CHANNELS)} channels ≠ 36"
    canon = {(min(a, b), max(a, b)) for a, b in CHANNELS}
    assert len(canon) == 36, "duplicate channels in table"
    for pair in [(10, 20), (10, 34), (10, 57), (20, 34), (20, 57), (34, 57)]:
        assert pair in canon, f"integration channel {pair} missing"
    gates_in_channels = {g for ch in CHANNELS for g in ch}
    assert gates_in_channels == set(range(1, 65)), (
        f"gates missing from channel table: {set(range(1,65)) - gates_in_channels}"
    )


if __name__ == "__main__":
    import traceback

    tests = [
        test_gate_wheel_spot_checks,
        test_all_gates_coverage,
        test_channel_inventory,
        test_personality_sun_gate_and_line,
        test_design_sun_gate_and_line,
        test_earth_is_sun_opposite,
        test_profile,
        test_type,
        test_authority,
        test_definition,
        test_defined_centers_count,
        test_head_undefined,
        test_incarnation_cross,
        test_variable,
        test_not_self_theme,
        test_design_date_approximate,
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
