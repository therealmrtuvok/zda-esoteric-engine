"""
Property/invariant checks that must hold for EVERY Human Design chart
(addendum 3, Part 2). Deliberately re-derives rules independently from the
engine's own helpers wherever possible, so a table/logic bug in src/ can't
hide inside the checker too.
Each check raises AssertionError with context on violation.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.human_design import HdChart
from src.hd_tables import CHANNELS, GATE_CENTER, CENTERS, GATE_WHEEL, opposite_gate
from src.crosses import angle_from_profile, ANGLE_LABELS
from src.ephemeris_core import calc_at_jd

STANDARD_BODIES = {
    "sun", "earth", "moon", "true_node", "south_node",
    "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
}

MOTORS = {"Sacral", "SolarPlexus", "Heart", "Root"}

VALID_TYPES = {"Generator", "ManifestingGenerator", "Manifestor",
               "Projector", "Reflector"}

VALID_PROFILES = {(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6),
                  (4, 1), (4, 6), (5, 1), (5, 2), (6, 2), (6, 3)}

# authority label → the center that must be the highest defined in hierarchy
AUTHORITY_EXPECT = [
    ("SolarPlexus", "Emotional (Solar Plexus)"),
    ("Sacral",      "Sacral"),
    ("Spleen",      "Splenic"),
    ("Heart",       "Ego / Heart"),
    ("G",           "Self-Projected"),
]


def _ctx(chart: HdChart) -> str:
    return (f"[birth_jd={chart.birth_julian_day:.4f} type={chart.type_} "
            f"profile={chart.profile} centers={sorted(chart.defined_centers)}]")


# ---------------------------------------------------------------------------
# Activation set
# ---------------------------------------------------------------------------
def check_activation_set(chart: HdChart):
    for label, acts in (("personality", chart.personality),
                        ("design", chart.design)):
        keys = set(acts.keys())
        assert keys == STANDARD_BODIES, (
            f"{label} bodies != standard 13: extra={keys - STANDARD_BODIES}, "
            f"missing={STANDARD_BODIES - keys} {_ctx(chart)}"
        )
        # Earth/South Node opposition at gate level
        assert acts["earth"].gate == opposite_gate(acts["sun"].gate), (
            f"{label} Earth gate {acts['earth'].gate} != opposite of Sun "
            f"{acts['sun'].gate} {_ctx(chart)}"
        )
        assert acts["south_node"].gate == opposite_gate(acts["true_node"].gate), (
            f"{label} South Node not opposite North Node {_ctx(chart)}"
        )


def check_design_arc(chart: HdChart):
    """Design Sun sits ~88° of solar arc before Personality Sun."""
    p_sun = calc_at_jd(chart.birth_julian_day)["sun"]["longitude"]
    d_sun = calc_at_jd(chart.design_julian_day)["sun"]["longitude"]
    arc = (p_sun - d_sun) % 360
    assert abs(arc - 88.0) < 0.01, (
        f"design solar arc {arc:.4f}° != 88° {_ctx(chart)}"
    )
    days = chart.birth_julian_day - chart.design_julian_day
    assert 80 < days < 100, f"design date {days:.1f} days before birth {_ctx(chart)}"


# ---------------------------------------------------------------------------
# Type & centers
# ---------------------------------------------------------------------------
def _independent_motor_to_throat(chart: HdChart) -> bool:
    """Re-derive motor-to-Throat over DEFINED channels only, independently."""
    if "Throat" not in chart.defined_centers:
        return False
    adj = {}
    for lo, hi in chart.defined_channels:
        ca, cb = GATE_CENTER[lo], GATE_CENTER[hi]
        if ca != cb:
            adj.setdefault(ca, set()).add(cb)
            adj.setdefault(cb, set()).add(ca)
    seen, stack = {"Throat"}, ["Throat"]
    while stack:
        for nb in adj.get(stack.pop(), ()):
            if nb in MOTORS:
                return True
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def check_type_rules(chart: HdChart):
    assert chart.type_ in VALID_TYPES, f"invalid type {chart.type_!r} {_ctx(chart)}"

    n = len(chart.defined_centers)
    assert 0 <= n <= 9, f"defined-center count {n} {_ctx(chart)}"

    is_reflector = chart.type_ == "Reflector"
    assert is_reflector == (n == 0), (
        f"Reflector iff zero centers violated: type={chart.type_} n={n} {_ctx(chart)}"
    )

    sacral = "Sacral" in chart.defined_centers
    motor_throat = _independent_motor_to_throat(chart)

    if chart.type_ in ("Generator", "ManifestingGenerator"):
        assert sacral, f"{chart.type_} without defined Sacral {_ctx(chart)}"
    else:
        assert not sacral or n == 0, (
            f"defined Sacral but type {chart.type_} {_ctx(chart)}"
        )
    if chart.type_ == "ManifestingGenerator":
        assert motor_throat, f"MG without motor-to-Throat {_ctx(chart)}"
    if chart.type_ == "Generator":
        assert not motor_throat, f"Generator WITH motor-to-Throat (should be MG) {_ctx(chart)}"
    if chart.type_ == "Manifestor":
        assert motor_throat and not sacral, f"Manifestor rule violated {_ctx(chart)}"
    if chart.type_ == "Projector":
        assert not sacral and not motor_throat and n > 0, (
            f"Projector rule violated {_ctx(chart)}"
        )


def check_authority(chart: HdChart):
    if chart.type_ == "Reflector":
        assert chart.authority == "Lunar", (
            f"Reflector authority {chart.authority!r} {_ctx(chart)}"
        )
        return
    for center, label in AUTHORITY_EXPECT:
        if center in chart.defined_centers:
            assert chart.authority == label, (
                f"authority {chart.authority!r} but highest defined is {center} "
                f"(expect {label!r}) {_ctx(chart)}"
            )
            return
    assert chart.authority == "Mental / None", (
        f"no authority center defined but authority={chart.authority!r} {_ctx(chart)}"
    )


# ---------------------------------------------------------------------------
# Profile & cross
# ---------------------------------------------------------------------------
def check_profile_and_cross(chart: HdChart):
    p_line = chart.personality["sun"].line
    d_line = chart.design["sun"].line
    assert 1 <= p_line <= 6 and 1 <= d_line <= 6, (
        f"profile lines out of range {p_line}/{d_line} {_ctx(chart)}"
    )
    assert (p_line, d_line) in VALID_PROFILES, (
        f"profile {p_line}/{d_line} not one of the 12 valid combinations {_ctx(chart)}"
    )
    assert chart.profile == f"{p_line}/{d_line}", (
        f"profile string {chart.profile!r} != sun lines {p_line}/{d_line} {_ctx(chart)}"
    )
    angle = angle_from_profile(p_line, d_line)
    assert chart.incarnation_cross.startswith(ANGLE_LABELS[angle]), (
        f"cross {chart.incarnation_cross!r} does not match angle {angle} "
        f"for profile {chart.profile} {_ctx(chart)}"
    )


# ---------------------------------------------------------------------------
# Structural integrity (tables + per-chart consistency)
# ---------------------------------------------------------------------------
def check_tables():
    """Chart-independent table integrity — run once per suite."""
    assert sorted(GATE_WHEEL) == list(range(1, 65)), "GATE_WHEEL not a permutation of 1-64"
    assert set(GATE_CENTER.keys()) == set(range(1, 65)), "GATE_CENTER must map all 64 gates"
    for g, c in GATE_CENTER.items():
        assert c in CENTERS, f"gate {g} maps to unknown center {c!r}"

    canon = {(min(a, b), max(a, b)) for a, b in CHANNELS}
    assert len(CHANNELS) == 36 and len(canon) == 36, "36 unique channels required"
    for a, b in CHANNELS:
        assert GATE_CENTER[a] != GATE_CENTER[b], (
            f"channel {a}-{b} connects a center to itself"
        )


def check_channel_consistency(chart: HdChart):
    for lo, hi in chart.defined_channels:
        assert lo in chart.all_gates and hi in chart.all_gates, (
            f"defined channel {lo}-{hi} has an unactivated gate {_ctx(chart)}"
        )
        assert GATE_CENTER[lo] in chart.defined_centers, (
            f"channel {lo}-{hi} defined but center {GATE_CENTER[lo]} not {_ctx(chart)}"
        )
        assert GATE_CENTER[hi] in chart.defined_centers, (
            f"channel {lo}-{hi} defined but center {GATE_CENTER[hi]} not {_ctx(chart)}"
        )
    # completeness: any channel whose gates are both active must be in defined_channels
    for a, b in CHANNELS:
        if a in chart.all_gates and b in chart.all_gates:
            assert (min(a, b), max(a, b)) in chart.defined_channels, (
                f"channel {a}-{b} has both gates active but is not defined {_ctx(chart)}"
            )
    # every defined center is touched by ≥1 defined channel
    touched = set()
    for lo, hi in chart.defined_channels:
        touched.add(GATE_CENTER[lo])
        touched.add(GATE_CENTER[hi])
    assert touched == chart.defined_centers, (
        f"defined centers {sorted(chart.defined_centers)} != channel-touched "
        f"{sorted(touched)} {_ctx(chart)}"
    )


ALL_CHART_CHECKS = [
    check_activation_set,
    check_design_arc,
    check_type_rules,
    check_authority,
    check_profile_and_cross,
    check_channel_consistency,
]


def check_chart(chart: HdChart):
    """Run every per-chart invariant; raises on first violation."""
    for fn in ALL_CHART_CHECKS:
        fn(chart)
