"""
Addendum 3 — Parts 2 & 3: invariant tests on known charts + the targeted
Chiron/asteroid regression guard. (Part 4 fuzz lives in test_fuzz.py.)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.human_design import compute_hd_chart, HD_PLANETS
from src.hd_transit import transit_state, ALL_BODIES
from src.hd_tables import longitude_to_activation, CHANNELS
from src.ephemeris_core import calc_at_jd, julian_day
from invariants import check_chart, check_tables, STANDARD_BODIES

KNOWN_CHARTS = [
    # Shannon (the original acceptance chart)
    dict(year=1994, month=10, day=16, hour_ut=13 + 57/60, lat=44.2333, lon=-76.5),
    # The live-validated Toronto chart (Split definition, 5 centers)
    dict(year=2001, month=3, day=8, hour_ut=19.5, lat=43.6532, lon=-79.3832),
    # The Chiron-guard Projector (see test_chiron_guard below)
    dict(year=1960, month=10, day=15, hour_ut=12.0, lat=44.2333, lon=-76.5),
]


def test_tables():
    check_tables()


def test_invariants_on_known_charts():
    for kc in KNOWN_CHARTS:
        chart = compute_hd_chart(**kc)
        check_chart(chart)   # raises with context on any violation


# ---------------------------------------------------------------------------
# Part 3 — targeted Chiron guard.
# 1960-10-15 12:00 UT, Kingston ON: a Splenic Projector by the standard 13
# bodies. Chiron sits in gate 55 at that moment; the natal chart holds gate 39.
# The OLD code (Chiron in HD_PLANETS) would have completed channel 39-55,
# defined the Solar Plexus, and misread this person as an EMOTIONAL Projector.
# This test fails on that code.
# ---------------------------------------------------------------------------
GUARD = dict(year=1960, month=10, day=15, hour_ut=12.0, lat=44.2333, lon=-76.5)


def test_chiron_guard_activation_set():
    chart = compute_hd_chart(**GUARD)
    assert set(chart.personality) == STANDARD_BODIES
    assert set(chart.design) == STANDARD_BODIES
    assert "chiron" not in HD_PLANETS and "juno" not in HD_PLANETS


def test_chiron_guard_would_have_completed_channel():
    """Prove the guard chart is actually a Chiron-sensitive case: Chiron's
    gate would complete 39-55 if it were (wrongly) included."""
    chart = compute_hd_chart(**GUARD)
    chiron_gates = set()
    for jd in (chart.birth_julian_day, chart.design_julian_day):
        lon = calc_at_jd(jd)["chiron"]["longitude"]
        chiron_gates.add(longitude_to_activation(lon)[0])
    # old code put Chiron in BOTH columns; its Design-moment gate is 55
    assert 55 in chiron_gates, (
        f"guard chart drifted: Chiron gates {sorted(chiron_gates)} lack 55"
    )
    assert 39 in chart.all_gates, "guard chart drifted: gate 39 not natal"
    assert 55 not in chart.all_gates, "guard broken: 55 active without Chiron?"


def test_chiron_guard_result_is_13_body_correct():
    chart = compute_hd_chart(**GUARD)
    assert (39, 55) not in chart.defined_channels, (
        "channel 39-55 defined — Chiron leaked into HD activations"
    )
    assert "SolarPlexus" not in chart.defined_centers, (
        "Solar Plexus defined — Chiron leaked into HD activations"
    )
    assert chart.type_ == "Projector"
    assert chart.authority == "Splenic", (
        f"authority {chart.authority!r} — the old Chiron bug read this chart "
        f"as Emotional"
    )


def test_asteroids_never_reach_transit_overlay_by_default():
    """Default transit overlay must use only the standard bodies."""
    chart = compute_hd_chart(**GUARD)
    jd = julian_day(2026, 7, 19, 12)
    state = transit_state(chart, jd)   # default bodies
    assert set(state["bodies"]) <= STANDARD_BODIES | set(ALL_BODIES)
    for b in state["transit_activations"]:
        assert b in STANDARD_BODIES, f"non-standard body {b!r} in transit overlay"


if __name__ == "__main__":
    import traceback

    tests = [
        test_tables,
        test_invariants_on_known_charts,
        test_chiron_guard_activation_set,
        test_chiron_guard_would_have_completed_channel,
        test_chiron_guard_result_is_13_body_correct,
        test_asteroids_never_reach_transit_overlay_by_default,
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
