"""
Acceptance test for the energy calendar layer: sky events and the meaning tables.

The astronomy here is checked against externally published values, in keeping
with the rule that the engine must not be the source of its own expectations.
The station and eclipse dates below come from published ephemerides, not from
running this code and recording what it said.

The meaning tables are checked for total coverage rather than for content,
because the failure mode they have is the one this project has already hit
four times: a mapping table that is silently short an entry, producing output
that is plausible and wrong. hd_meanings.validate() and
numerology_meanings.validate() prove coverage by enumeration.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date

from src.ephemeris_core import (julian_day, jd_to_datetime_tuple,
                                find_stations, find_lunations,
                                find_sign_ingresses, find_eclipses)
from src.numerology import personal_year
from src.interpretations import PERSONAL_YEARS
import src.hd_meanings as hd_meanings
import src.numerology_meanings as num_meanings
from src.sky_events import mundane_events, scan_aspect_windows

JD_START = julian_day(2026, 9, 1, 0)
JD_END = julian_day(2027, 4, 30, 0)


def _iso(jd):
    y, m, d, _h = jd_to_datetime_tuple(jd)
    return f"{y:04d}-{m:02d}-{d:02d}"


# ---------------------------------------------------------------------------
# Sky events against published values
# ---------------------------------------------------------------------------
def test_mercury_stations():
    """Mercury retrograde 24 Oct to 13 Nov 2026, and 9 Feb to 3 Mar 2027."""
    st = find_stations("mercury", JD_START, JD_END)
    got = [(_iso(s["jd"]), s["direction"]) for s in st]
    assert got == [("2026-10-24", "retrograde"), ("2026-11-13", "direct"),
                   ("2027-02-09", "retrograde"), ("2027-03-03", "direct")], got


def test_mars_retrograde_period():
    """Mars retrograde 10 Jan to 1 Apr 2027."""
    st = find_stations("mars", JD_START, JD_END)
    got = [(_iso(s["jd"]), s["direction"]) for s in st]
    assert got == [("2027-01-10", "retrograde"), ("2027-04-01", "direct")], got


def test_luminaries_never_station():
    """A silently empty list would hide a caller's mistake, so this raises."""
    for body in ("sun", "moon"):
        try:
            find_stations(body, JD_START, JD_END)
        except ValueError:
            continue
        raise AssertionError(f"{body} should refuse to be scanned for stations")


def test_eclipses():
    """Annular solar 6 Feb 2027, penumbral lunar 20 Feb 2027."""
    ec = [(_iso(e["jd"]), e["body"], e["kind"])
          for e in find_eclipses(JD_START, JD_END)]
    assert ec == [("2027-02-06", "sun", "annular"),
                  ("2027-02-20", "moon", "penumbral")], ec


def test_lunation_count_and_alternation():
    """Sixteen lunations in eight months, strictly alternating new and full."""
    lu = find_lunations(JD_START, JD_END)
    assert len(lu) == 16, len(lu)
    phases = [x["phase"] for x in lu]
    for a, b in zip(phases, phases[1:]):
        assert a != b, phases


def test_retrograde_ingress_is_caught():
    """
    Mars stations retrograde at 10 Virgo and turns direct at 20 Leo, so it
    crosses the Leo/Virgo boundary backwards on 21 Feb 2027. A forward-only
    scanner drops this, and the chart then shows Mars in the wrong sign for
    five weeks.
    """
    ing = find_sign_ingresses("mars", JD_START, JD_END)
    back = [i for i in ing if i["direction"] == "retrograde"]
    assert len(back) == 1, ing
    assert _iso(back[0]["jd"]) == "2027-02-21", _iso(back[0]["jd"])
    assert back[0]["sign_index"] == 4, back[0]   # Leo


def test_mundane_events_are_date_sorted_and_labelled():
    ev = mundane_events(JD_START, JD_END)
    assert ev, "no events found in an eight month range"
    assert [e["jd"] for e in ev] == sorted(e["jd"] for e in ev)
    kinds = {e["kind"] for e in ev}
    assert kinds == {"station", "lunation", "eclipse", "ingress"}, kinds
    # An eclipse is also a lunation. It must be reported once, as the eclipse.
    eclipse_dates = {e["date"] for e in ev if e["kind"] == "eclipse"}
    lunation_dates = {e["date"] for e in ev if e["kind"] == "lunation"}
    assert not (eclipse_dates & lunation_dates), eclipse_dates & lunation_dates


def test_aspect_window_brackets_its_exact_dates():
    natal = {"sun": 100.0, "moon": 250.0, "ascendant": 15.0}
    wins = scan_aspect_windows(natal, JD_START, JD_END)
    assert wins, "no aspect windows in an eight month range"
    for w in wins:
        assert w["start"] <= w["end"], w
        for e in w["exact"]:
            assert w["start"] <= e <= w["end"], w
        assert w["passes"] == len(w["exact"]), w


# ---------------------------------------------------------------------------
# Meaning table coverage
# ---------------------------------------------------------------------------
def test_sun_rise_set_is_ordered_and_refuses_polar_night():
    """
    Sunrise before sunset, a plausible day length at temperate latitude, and a
    loud failure rather than a meaningless number inside the polar circles,
    where planetary hours are undefined.
    """
    from src.ephemeris_core import sun_rise_set, jd_to_datetime_tuple

    rise, sett = sun_rise_set(2026, 10, 15, 45.0, -75.0)
    assert rise < sett, (rise, sett)
    day_hours = (sett - rise) * 24
    assert 10.0 < day_hours < 12.0, day_hours   # mid-October, mid-latitude

    # equinox: close to twelve hours anywhere temperate
    r2, s2 = sun_rise_set(2026, 9, 22, 45.0, -75.0)
    assert 11.7 < (s2 - r2) * 24 < 12.5, (s2 - r2) * 24

    # Svalbard in midwinter: the Sun does not rise
    try:
        sun_rise_set(2026, 12, 21, 78.2, 15.6)
    except ValueError:
        pass
    else:
        raise AssertionError("polar night should raise, not return a number")


def test_hd_meaning_tables_complete():
    problems = hd_meanings.validate()
    assert not problems, "\n".join(problems)


def test_numerology_meaning_tables_complete():
    problems = num_meanings.validate()
    assert not problems, "\n".join(problems)


def test_personal_year_text_covers_every_reachable_value():
    """
    Regression. reduce() keeps master numbers, so personal_year() returns 11
    and 22 for some birth dates. PERSONAL_YEARS held only 1 to 9, and the
    lookup uses .get() with a default, so those years returned empty
    interpretation text and no error.
    """
    reachable = set()
    for month in range(1, 13):
        for dom in (1, 9, 16, 28):
            try:
                birth = date(1975, month, dom)
            except ValueError:
                continue
            for year in range(2020, 2040):
                reachable.add(personal_year(birth, date(year, 12, 1)))
    missing = sorted(reachable - set(PERSONAL_YEARS))
    assert not missing, f"personal years with no text: {missing}"


def test_every_chart_property_has_non_empty_text():
    """
    The Design Chart panel opens an explanation for Type, Profile, Authority,
    Definition, Cross, Variable and every centre. A missing table entry would
    render a heading with nothing under it, which is the same silent-blank
    failure as the personal year bug.

    Run over the test_fixtures charts rather than invented birth data, because
    those are deliberately chosen to cover all five Types, every definition
    class and the Reflector zero-centres edge. An earlier version of this test
    used six arbitrary births and reached only two Types, which is exactly the
    blind spot the fixtures exist to close.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_fixtures import FIXTURES
    from src.human_design import compute_hd_chart, hd_chart_to_dict
    from src.interpretations import (interpret_human_design, interpret_cross,
                                     interpret_variable)

    seen_types, seen_defs = set(), set()
    for fx in FIXTURES:
        who = fx["name"]
        hd = compute_hd_chart(**fx["birth"])
        d = hd_chart_to_dict(hd)
        out = interpret_human_design(d)
        seen_types.add(hd.type_)
        seen_defs.add(hd.definition)

        for key in ("type", "definition", "authority"):
            assert out[key].get("name"), f"{who}: {key} has no name"
            assert out[key].get("body"), f"{who}: {key} has no body text"

        assert out["profile"]["lines"], f"{who}: profile has no lines"
        for line in out["profile"]["lines"]:
            assert line["name"] and line["text"], f"{who}: blank line {line}"

        assert len(out["centers"]) == 9, f"{who}: {len(out['centers'])} centres"
        for c in out["centers"]:
            assert c["text"], f"{who}: centre {c['center']} has no text"

        cross = interpret_cross(d)
        assert cross["angle"] in ("Right Angle", "Juxtaposition", "Left Angle"), \
            f"{who}: unrecognised angle in {cross['name']!r}"
        assert cross["angle_text"], f"{who}: angle {cross['angle']} has no text"
        assert len(cross["gates"]) == 4, f"{who}: {cross['gates']}"

        var = interpret_variable(d)
        assert var["letters"], f"{who}: variable {var['variable']!r} parsed to nothing"

    assert len(seen_types) == 5, f"fixtures no longer cover all 5 types: {seen_types}"
    assert len(seen_defs) >= 3, f"only saw definitions {seen_defs}"


def test_quarters_partition_the_wheel():
    """
    Four quarters of 16 gates each, covering all 64 exactly once, derived from
    GATE_WHEEL rather than typed out. A hand-written quarter table is precisely
    the kind of mapping that has broken this engine before.
    """
    from src.hd_tables import GATE_QUARTER, GATE_WHEEL, QUARTER_STARTS
    from collections import Counter
    assert len(GATE_QUARTER) == 64, len(GATE_QUARTER)
    assert set(GATE_QUARTER) == set(range(1, 65))
    counts = Counter(GATE_QUARTER.values())
    assert set(counts) == set(QUARTER_STARTS.values()), counts
    assert all(v == 16 for v in counts.values()), counts
    # each quarter is 16 consecutive gates on the wheel, not a scattered set
    for start_gate, name in QUARTER_STARTS.items():
        i = GATE_WHEEL.index(start_gate)
        run = [GATE_WHEEL[(i + j) % 64] for j in range(16)]
        assert all(GATE_QUARTER[g] == name for g in run), (name, run)


def test_cross_reads_only_the_personality_sun_quarter():
    """
    The four cross gates sit about 88, 180 and 268 degrees apart and the
    quarters are 90 degree blocks, so a four-quarter spread is the ordinary
    case. Guard against a future version presenting it as meaningful: the
    reading must key off the Personality Sun alone.
    """
    from src.human_design import compute_hd_chart, hd_chart_to_dict
    from src.interpretations import interpret_cross
    from src.hd_tables import GATE_QUARTER

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_fixtures import FIXTURES

    for fx in FIXTURES:
        d = hd_chart_to_dict(compute_hd_chart(**fx["birth"]))
        x = interpret_cross(d)
        p_sun = d["personality"]["sun"]["gate"]
        assert x["quarter"] == GATE_QUARTER[p_sun], (fx["name"], x["quarter"])
        assert x["quarter_text"], f"{fx['name']}: quarter has no text"
        assert all("quarter" in g for g in x["gates"]), fx["name"]


def test_structure_classification_is_exhaustive_and_consistent():
    """
    Completing any channel must classify as exactly one of bridge, opens,
    local or already, for every fixture chart including the Reflector, which
    has no components to bridge at all.
    """
    from src.human_design import compute_hd_chart
    from src.hd_structure import islands, classify_completion, bridge_gates
    from src.hd_tables import CHANNELS, GATE_CENTER

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_fixtures import FIXTURES

    valid = {"bridge", "opens", "local", "already"}
    for fx in FIXTURES:
        hd = compute_hd_chart(**fx["birth"])
        isl = islands(hd)
        assert sum(len(i["centers"]) for i in isl) == len(hd.defined_centers), \
            f"{fx['name']}: islands do not partition the defined centres"
        assert [i["index"] for i in isl] == list(range(1, len(isl) + 1)), fx["name"]

        for a, b in CHANNELS:
            c = classify_completion(hd, a, b)
            assert c["effect"] in valid, (fx["name"], a, b, c)
            if c["effect"] == "already":
                assert (min(a, b), max(a, b)) in hd.defined_channels
            if c["effect"] == "bridge":
                assert c["joins"] and len(c["joins"]) == 2, (fx["name"], a, b, c)
                assert GATE_CENTER[a] in hd.defined_centers, (fx["name"], a, b)
                assert GATE_CENTER[b] in hd.defined_centers, (fx["name"], a, b)
            if c["effect"] == "opens":
                assert c["defines"], (fx["name"], a, b, c)
                assert all(x not in hd.defined_centers for x in c["defines"])

        # every bridge gate must be one the chart does not carry, and must
        # genuinely bridge when checked from the other direction
        for gate, b in bridge_gates(hd).items():
            assert gate not in hd.all_gates, (fx["name"], gate)
            assert b["completes_your_gate"] in hd.all_gates, (fx["name"], gate)
            again = classify_completion(hd, gate, b["completes_your_gate"])
            assert again["effect"] == "bridge", (fx["name"], gate, again)


def test_a_split_chart_has_bridge_gates_and_a_single_definition_has_none():
    """
    Sanity on the whole idea: bridging only exists where there is more than
    one island. Single Definition charts must report no bridge gates at all.
    """
    from src.human_design import compute_hd_chart
    from src.hd_structure import islands, bridge_gates

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_fixtures import FIXTURES

    checked_single = checked_split = False
    for fx in FIXTURES:
        hd = compute_hd_chart(**fx["birth"])
        n = len(islands(hd))
        bg = bridge_gates(hd)
        if n <= 1:
            assert not bg, f"{fx['name']}: {n} island(s) but bridge gates {list(bg)}"
            checked_single = True
        else:
            checked_split = True
            for b in bg.values():
                assert len(b["joins"]) == 2 and b["joins"][0] != b["joins"][1], b
    assert checked_split, "no split fixture exercised"
    assert checked_single, "no single-definition or Reflector fixture exercised"


def test_population_shares_match_what_the_engine_actually_produces():
    """
    interpretations.py tells a reader what share of people have their Type and
    Definition. Those numbers were inherited, not measured, and one of them was
    wrong: Reflector and No Definition were both described as "under 1%" when
    the engine produces about 1.1%.

    Rather than trust a figure, measure it. Sampled charts are uniform over
    date, time and place, which is not the real human birth distribution, so
    the tolerance is deliberately loose. It is tight enough to catch a claim
    that is simply false.
    """
    import random
    from collections import Counter
    from src.human_design import compute_hd_chart

    random.seed(20260826)
    N = 600
    types, defs = Counter(), Counter()
    for _ in range(N):
        hd = compute_hd_chart(random.randint(1940, 2015), random.randint(1, 12),
                              random.randint(1, 28), random.uniform(0, 24),
                              random.uniform(-55, 62), random.uniform(-180, 180))
        types[hd.type_] += 1
        defs[hd.definition] += 1

    # (label, low, high) as a percentage, from a 4000-chart measurement
    expected = [
        (types, "Generator", 30, 42), (types, "ManifestingGenerator", 28, 38),
        (types, "Projector", 15, 25), (types, "Manifestor", 6, 14),
        (types, "Reflector", 0.2, 3),
        (defs, "Split Definition", 41, 52), (defs, "Single Definition", 35, 46),
        (defs, "Triple Split", 7, 16), (defs, "Quadruple Split", 0.1, 3),
    ]
    for counter, label, lo, hi in expected:
        pct = counter[label] / N * 100
        assert lo <= pct <= hi, f"{label} came out at {pct:.1f}%, expected {lo} to {hi}"

    # the two superlatives the copy actually asserts
    assert defs.most_common(1)[0][0] == "Split Definition", \
        f"copy calls Split the most common, but got {defs.most_common(3)}"
    rarest = min((d for d in defs if defs[d]), key=lambda d: defs[d])
    assert defs["Quadruple Split"] <= defs["No Definition"], \
        "copy calls Quadruple Split the rarest configuration"


def test_describe_channel_names_the_held_and_supplied_halves():
    d = hd_meanings.describe_channel(2, 14, held_gate=2)
    assert d["held_gate"] == 2 and d["supplied_gate"] == 14, d
    assert d["centers"] == ["G", "Sacral"], d["centers"]
    assert d["standing_condition"] == hd_meanings.GATE_MEANINGS[2]["hanging"]
    # and the same channel from the other side
    d2 = hd_meanings.describe_channel(14, 2, held_gate=14)
    assert d2["held_gate"] == 14 and d2["supplied_gate"] == 2, d2
    assert d2["channel"] == d["channel"] == "2-14"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
