"""
Tests for the Incarnation Cross name table (src/crosses.py).

The CROSSES table was built from two independent reference lists
(ahumandesign.com and loveyourhumandesign.com, which agreed on all 192
base names) and spot-checked against a third (humandesign.zone).
These tests enforce the structural invariants and pin known entries.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.crosses import CROSSES, angle_from_profile, cross_name, ANGLE_LABELS
from src.hd_tables import opposite_gate, GATE_WHEEL

_IDX = {g: i for i, g in enumerate(GATE_WHEEL)}


def test_earth_opposition():
    """Every key: earth gates are the wheel-opposites of the sun gates."""
    for (p_sun, p_earth, d_sun, d_earth, angle) in CROSSES:
        assert opposite_gate(p_sun) == p_earth, \
            f"({p_sun},{p_earth},{d_sun},{d_earth},{angle}): p_earth != opposite({p_sun})"
        assert opposite_gate(d_sun) == d_earth, \
            f"({p_sun},{p_earth},{d_sun},{d_earth},{angle}): d_earth != opposite({d_sun})"


def test_valid_angles():
    """Every key's angle is RAC, JUX, or LAC."""
    for key in CROSSES:
        assert key[4] in ANGLE_LABELS, f"bad angle in key {key}"


def test_design_sun_wheel_offset():
    """
    The Design Sun is ~88 degrees of solar arc before the Personality Sun.
    On the 64-gate wheel that is exactly 16 gates back for Right Angle
    (personality lines 1-3) and 15 gates back for Juxtaposition/Left Angle
    (personality lines 4-6).
    """
    for (p_sun, _, d_sun, _, angle) in CROSSES:
        offset = (_IDX[p_sun] - _IDX[d_sun]) % 64
        expected = 16 if angle == "RAC" else 15
        assert offset == expected, \
            f"{angle} cross at sun gate {p_sun}: design sun {d_sun} is {offset} gates back, expected {expected}"


def test_full_coverage():
    """One RAC, one JUX, one LAC entry per Personality Sun gate → 192 total."""
    seen = {}
    for (p_sun, _, _, _, angle) in CROSSES:
        assert (p_sun, angle) not in seen, f"duplicate entry for sun gate {p_sun} {angle}"
        seen[(p_sun, angle)] = True
    missing = [(g, a) for g in range(1, 65) for a in ("RAC", "JUX", "LAC")
               if (g, a) not in seen]
    assert not missing, f"missing entries: {missing}"
    assert len(CROSSES) == 192, f"expected 192 entries, got {len(CROSSES)}"


def test_angle_from_profile():
    """All 11 valid profiles map to the right angle; invalid raises."""
    expected = {
        (1, 3): "RAC", (1, 4): "RAC", (2, 4): "RAC", (2, 5): "RAC",
        (3, 5): "RAC", (3, 6): "RAC",
        (4, 1): "JUX",
        (4, 6): "LAC", (5, 1): "LAC", (5, 2): "LAC",
        (6, 2): "LAC", (6, 3): "LAC",
    }
    assert len(expected) == 12  # 12 line-pairs = 11 named profiles + 4/1 JUX kept distinct
    for (pl, dl), angle in expected.items():
        assert angle_from_profile(pl, dl) == angle, f"profile {pl}/{dl}"
    for bad in [(1, 1), (2, 2), (3, 4), (6, 5), (0, 3), (7, 1)]:
        try:
            angle_from_profile(*bad)
            assert False, f"profile {bad} should raise ValueError"
        except ValueError:
            pass


def test_confirmed_maya():
    """The one chart-verified entry."""
    assert cross_name(32, 42, 62, 61, 3, 5) == \
        "Right Angle Cross of Maya (32/42 | 62/61)"


def test_known_crosses():
    """
    Entries on which both primary sources agreed, spot-checked against a
    third source (humandesign.zone) — spanning all three angles.
    """
    known = [
        # (p_sun, p_earth, d_sun, d_earth, p_line, d_line, expected)
        (13, 7, 1, 2, 1, 3, "Right Angle Cross of the Sphinx (13/7 | 1/2)"),
        (1, 2, 7, 13, 2, 4, "Right Angle Cross of the Sphinx (1/2 | 7/13)"),
        (9, 16, 64, 63, 4, 1, "Juxtaposition Cross of Focus (9/16 | 64/63)"),
        (59, 55, 16, 9, 4, 1, "Juxtaposition Cross of Strategy (59/55 | 16/9)"),
        (2, 1, 49, 4, 5, 1, "Left Angle Cross of Defiance (2/1 | 49/4)"),
        (51, 57, 61, 62, 6, 2, "Left Angle Cross of the Clarion (51/57 | 61/62)"),
    ]
    for p_sun, p_earth, d_sun, d_earth, pl, dl, expected in known:
        got = cross_name(p_sun, p_earth, d_sun, d_earth, pl, dl)
        assert got == expected, f"expected {expected!r}, got {got!r}"


def test_no_pending_fallbacks():
    """Every geometrically valid (sun gate, angle) combination resolves to a name."""
    for g in range(1, 65):
        for angle, (pl, dl) in (("RAC", (3, 5)), ("JUX", (4, 1)), ("LAC", (5, 1))):
            offset = 16 if angle == "RAC" else 15
            d_sun = GATE_WHEEL[(_IDX[g] - offset) % 64]
            name = cross_name(g, opposite_gate(g), d_sun, opposite_gate(d_sun), pl, dl)
            assert "name pending" not in name, f"unnamed cross: gate {g} {angle}"


if __name__ == "__main__":
    import traceback

    tests = [
        test_earth_opposition,
        test_valid_angles,
        test_design_sun_wheel_offset,
        test_full_coverage,
        test_angle_from_profile,
        test_confirmed_maya,
        test_known_crosses,
        test_no_pending_fallbacks,
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

    print(f"\nCROSSES filled: {len(CROSSES)}/192")
    print(f"{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
