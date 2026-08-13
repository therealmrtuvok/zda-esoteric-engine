"""
Acceptance tests — transit overlays & projection timeline (addendum 2, A & B).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ephemeris_core import julian_day, calc_at_jd
from src.human_design import compute_hd_chart
from src.hd_transit import (
    transit_state, scan_channel_windows, _completed_channels_on,
    ALL_BODIES, SLOW_BODIES,
)
from src.hd_tables import longitude_to_activation

BIRTH = dict(year=1961, month=8, day=5, hour_ut=5 + 24/60,
             lat=21.3069, lon=-157.8583)
_hd = compute_hd_chart(**BIRTH)
BIRTH_JD = _hd.birth_julian_day


# ---------------------------------------------------------------------------
# A. Transit merge
# ---------------------------------------------------------------------------
def test_transit_sun_gate_at_equinox():
    """
    March 2026 equinox (almanac 2026-03-20 ~14:46 UT): Sun at 0° Aries,
    which sits inside Gate 25 on the Alchemy Wheel (gate 25 spans
    28°15' Pisces – 3°52.5' Aries). Sun longitude must be <2' from 0° Aries
    and map to gate 25.
    """
    jd = julian_day(2026, 3, 20, 14 + 46/60)
    sun_lon = calc_at_jd(jd)["sun"]["longitude"]
    diff = min(sun_lon, 360 - sun_lon)
    assert diff < 2/60, f"equinox Sun {diff*60:.2f}' from 0° Aries"
    gate, line, *_ = longitude_to_activation(sun_lon)
    assert gate == 25, f"equinox Sun gate {gate} ≠ 25"


def test_merge_at_birth_reproduces_natal():
    """Transit at t=birth adds nothing: no transitCompleted channels,
    transit-inclusive centers == natal centers."""
    state = transit_state(_hd, BIRTH_JD, bodies=ALL_BODIES)

    completed = [k for k, v in state["channels"].items() if v["transitCompleted"]]
    assert completed == [], f"transit at birth completed channels: {completed}"

    assert state["centersTransit"] == state["centersNatal"], (
        "transit-inclusive centers differ from natal at t=birth"
    )
    # every natal-defined channel must still be defined in the merge
    for lo, hi in _hd.defined_channels:
        assert state["channels"][f"{lo}-{hi}"]["defined"]


def test_state_object_shape():
    jd = julian_day(2026, 7, 19, 12)
    state = transit_state(_hd, jd)
    assert set(state["gates"].keys()) == set(range(1, 65))
    assert len(state["channels"]) == 36
    for v in state["gates"].values():
        assert set(v["sources"]) <= {"personality", "design", "transit"}
        assert v["activated"] == bool(v["sources"])
    for v in state["channels"].values():
        if v["transitCompleted"]:
            assert v["defined"] and "transit" in v["by"]


def test_transit_completion_requires_transit_gate():
    """Every transitCompleted channel must have at least one gate that the
    natal chart lacks and a transiting body supplies."""
    jd = julian_day(2026, 7, 19, 12)
    state = transit_state(_hd, jd)
    for key, v in state["channels"].items():
        if not v["transitCompleted"]:
            continue
        lo, hi = map(int, key.split("-"))
        assert (lo, hi) not in _hd.defined_channels
        missing = [g for g in (lo, hi) if g not in _hd.all_gates]
        assert missing, f"channel {key} marked transitCompleted but natal has both gates"
        for g in missing:
            assert "transit" in state["gates"][g]["sources"]


# ---------------------------------------------------------------------------
# B. Timeline scanner
# ---------------------------------------------------------------------------
def test_saturn_aries_ingress_almanac():
    """Almanac: Saturn enters Aries (crosses 0°) on 2026-02-14."""
    lon_before = calc_at_jd(julian_day(2026, 2, 13, 0))["saturn"]["longitude"]
    lon_after = calc_at_jd(julian_day(2026, 2, 15, 12))["saturn"]["longitude"]
    assert lon_before > 355, f"Saturn on Feb 13 at {lon_before:.2f}° (should be late Pisces)"
    assert lon_after < 1, f"Saturn on Feb 15 at {lon_after:.2f}° (should be early Aries)"


def test_scanner_boundary_consistency():
    """Each window's start day must be the first day the channel is complete:
    complete at start, not complete at start - 1 day."""
    jd_start = julian_day(2026, 1, 1, 12)
    jd_end = julian_day(2028, 1, 1, 12)
    windows = scan_channel_windows(_hd, jd_start, jd_end)
    assert windows, "no transit windows found for 2026-2028 with slow bodies"

    checked = 0
    for w in windows:
        ch = tuple(map(int, w["channel"].split("-")))
        active_at_start = _completed_channels_on(_hd, w["start_jd"], SLOW_BODIES)
        assert ch in active_at_start, f"{w['channel']} not complete on its start day"
        if w["start_jd"] > jd_start:  # interior boundary only
            active_before = _completed_channels_on(_hd, w["start_jd"] - 1, SLOW_BODIES)
            assert ch not in active_before, (
                f"{w['channel']} already complete the day before {w['start']}"
            )
            checked += 1
    assert checked >= 1, "no interior window boundaries to verify"


def test_scanner_slow_default_excludes_fast():
    jd_start = julian_day(2026, 6, 1, 12)
    jd_end = julian_day(2026, 6, 30, 12)
    windows = scan_channel_windows(_hd, jd_start, jd_end)
    for w in windows:
        for planet in w["planets"]:
            assert planet in SLOW_BODIES + ["south_node"], (
                f"fast body {planet} in default slow scan"
            )


def test_scanner_output_shape():
    jd_start = julian_day(2026, 1, 1, 12)
    jd_end = julian_day(2027, 1, 1, 12)
    windows = scan_channel_windows(_hd, jd_start, jd_end)
    for w in windows:
        assert set(w) >= {"channel", "planets", "start", "end", "center_effect"}
        assert w["start"] <= w["end"]


if __name__ == "__main__":
    import traceback

    tests = [
        test_transit_sun_gate_at_equinox,
        test_merge_at_birth_reproduces_natal,
        test_state_object_shape,
        test_transit_completion_requires_transit_gate,
        test_saturn_aries_ingress_almanac,
        test_scanner_boundary_consistency,
        test_scanner_slow_default_excludes_fast,
        test_scanner_output_shape,
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
