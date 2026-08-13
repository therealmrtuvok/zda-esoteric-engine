"""
Regression fixtures — verified public-figure Human Design charts.

Complements test_acceptance_hd.py (reference chart: Projector / Emotional /
Single Definition / Left Angle) with coverage it cannot provide:

  Types:        Projector (Obama), Manifestor (Ra Uru Hu, Aldrin),
                ManifestingGenerator (Jolie), Reflector (Geller)
  Authorities:  Sacral (Madonna), Splenic (Ra, Aldrin), Lunar (Geller),
                Emotional (Obama, Oprah, Jolie)
  Definitions:  Single (Ra, Obama, Aldrin), Split (Madonna, Jolie),
                Triple Split (Oprah), No Definition (Geller)
  Angles:       Left Angle (Ra, Madonna, Obama), Juxtaposition 4/1 (Aldrin),
                Right Angle (Oprah, Jolie)
  Defined Head: Madonna, Oprah, Aldrin (the reference chart's Head is open)
  Note: Obama also serves as the primary acceptance chart in test_acceptance_*.

Sourcing: birth data from Astro-Databank (Rodden AA/A) or, for Ra Uru Hu,
from his own chart published by the Jovian Archive / humandesignsystem.com,
which prints both local and UT times.  Expected chart values were taken from
one Human Design source and cross-checked against a second independent one;
fixtures whose sources disagreed (e.g. Sandra Bullock, Rodden C) were dropped.

Two assertion tiers per fixture:
  "expect" — values stated by the external HD sources (known-correct).
  "pin"    — engine-derived values recorded as regression pins for charts
             whose sourced headline fields all match exactly; these guard
             against silent behavioural drift but were not independently
             published (mainly center sets).

Every fixture chart must also pass the full invariant suite (invariants.py).
"""

import sys, os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TESTS_DIR))   # repo root  -> src package
sys.path.insert(0, TESTS_DIR)                    # tests dir  -> invariants

from src.human_design import compute_hd_chart
from invariants import check_chart, check_tables

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
FIXTURES = [
    {
        # Ra Uru Hu (Robert Allan Krakower), founder of Human Design.
        # Born 9 April 1948, 00:14 EST (= 05:14 UT), Montréal, Canada.
        # Birth + design times printed on his own published chart:
        #   humandesignsystem.com/archive/charts/HuRaUru.pdf ("05:14 UT",
        #   "00:14 EST April 9, 1948, Montréal"; design 1948-01-12 13:28 UT).
        # Chart values cross-checked: flowwithhumandesign.com (Manifestor,
        # 5/1, Splenic, Single Definition, Left Angle Cross of the Clarion
        # (51/57 | 61/62)) and app.humandesign.ai celebrity library (same).
        # Montréal was NOT yet on DST on Apr 9 1948 (DST began late April).
        "name": "Ra Uru Hu",
        "coverage": "Manifestor / Splenic / Single / Left Angle",
        "birth": dict(year=1948, month=4, day=9, hour_ut=5 + 14 / 60,
                      lat=45.5088, lon=-73.5540),
        "expect": {
            "type": "Manifestor",
            "authority": "Splenic",
            "profile": "5/1",
            "definition": "Single Definition",
            "cross": "Left Angle Cross of the Clarion (51/57 | 61/62)",
        },
        "pin": {
            "defined_centers": {"Ajna", "G", "Heart", "Spleen", "Throat"},
        },
    },
    {
        # Barack Obama.
        # Born 4 August 1961, 19:24 AHST (UTC-10), Honolulu, HI — Rodden AA
        # (birth certificate, Astro-Databank).  19:24 -10h -> 05:24 UT Aug 5.
        # Chart values: transcendzen.com + nicolelaino.com (6/2 Projector);
        # thehumandesignsystem.com blog "Design of a Projector President"
        # (Emotional Projector, "just one channel from the Root Center to
        # the Emotional System" => only Root + Solar Plexus defined, hence
        # Single Definition); loveyourhumandesign.com (Projector, cross
        # description matching the Left Angle Cross of Refinement).
        "name": "Barack Obama",
        "coverage": "Projector / Emotional / Single / Left Angle / 6-2",
        "birth": dict(year=1961, month=8, day=5, hour_ut=5.4,
                      lat=21.3069, lon=-157.8583),
        "expect": {
            "type": "Projector",
            "authority": "Emotional (Solar Plexus)",
            "profile": "6/2",
            "definition": "Single Definition",
            "cross_prefix": "Left Angle",
            "defined_centers": {"Root", "SolarPlexus"},
        },
        "pin": {
            "cross": "Left Angle Cross of Refinement (33/19 | 2/1)",
        },
    },
    {
        # Madonna (Madonna Louise Ciccone).
        # Born 16 August 1958, 07:05 EST, Bay City, MI — Rodden AA
        # (Astro-Databank).  Michigan did not observe DST in 1958 (EST
        # year-round), so 07:05 EST -> 12:05 UT.
        # Chart values: flowwithhumandesign.com (Generator, 5/1, Sacral,
        # Split Definition, Left Angle Cross of Revolution (4/49 | 8/14));
        # cross-checked "5/1 Sacral Generator" via juliettestapleton.com and
        # the Madonna chart readings on humandesign.ai / YouTube HD readings.
        # Head is DEFINED here (63-4 Channel of Logic; personality Sun gate 4).
        "name": "Madonna",
        "coverage": "Generator / SACRAL / Split / Left Angle / defined Head",
        "birth": dict(year=1958, month=8, day=16, hour_ut=12 + 5 / 60,
                      lat=43.5945, lon=-83.8889),
        "expect": {
            "type": "Generator",
            "authority": "Sacral",
            "profile": "5/1",
            "definition": "Split Definition",
            "cross": "Left Angle Cross of Revolution (4/49 | 8/14)",
        },
        "pin": {
            "defined_centers": {"Ajna", "G", "Head", "Sacral", "Throat"},
            "head_defined": True,
        },
    },
    {
        # Oprah Winfrey.
        # Born 29 January 1954, 04:30 CST (UTC-6), Kosciusko, MS — Rodden A
        # (Astro-Databank, time confirmed by Oprah).  04:30 -> 10:30 UT.
        # Chart values: flowwithhumandesign.com (Generator, 2/4, Emotional —
        # Solar Plexus, Triple Split Definition, Right Angle Cross of the
        # Four Ways (19/33 | 44/24)); cross-checked humandesignforsuccess.com
        # + souljourneyhumandesign.com (2/4 Emotional Generator, RAX Four
        # Ways, triple split, open Ego).
        "name": "Oprah Winfrey",
        "coverage": "Generator / Emotional / TRIPLE SPLIT / Right Angle / defined Head",
        "birth": dict(year=1954, month=1, day=29, hour_ut=10.5,
                      lat=33.0580, lon=-89.5876),
        "expect": {
            "type": "Generator",
            "authority": "Emotional (Solar Plexus)",
            "profile": "2/4",
            "definition": "Triple Split",
            "cross": "Right Angle Cross of the Four Ways (19/33 | 44/24)",
        },
        "pin": {
            "defined_centers": {"Ajna", "G", "Head", "Root", "Sacral",
                                "SolarPlexus", "Spleen"},
            "head_defined": True,
            "undefined_contains": {"Heart"},   # sourced: "open ego center"
        },
    },
    {
        # Angelina Jolie.
        # Born 4 June 1975, 09:09 PDT (UTC-7), Los Angeles, CA — Rodden AA
        # (Astro-Databank, birth certificate).  09:09 -> 16:09 UT.
        # Chart values: flowwithhumandesign.com (Manifesting Generator, 3/5,
        # Emotional (Solar Plexus), Split Definition, Right Angle Cross of
        # Consciousness (35/5 | 63/64)); cross-checked humandesignsystem.co
        # ("3/5 Manifesting Generator - Emotional") and hd-chart.com.
        "name": "Angelina Jolie",
        "coverage": "MANIFESTING GENERATOR / Emotional / Split / Right Angle",
        "birth": dict(year=1975, month=6, day=4, hour_ut=16.15,
                      lat=34.0522, lon=-118.2437),
        "expect": {
            "type": "ManifestingGenerator",
            "authority": "Emotional (Solar Plexus)",
            "profile": "3/5",
            "definition": "Split Definition",
            "cross": "Right Angle Cross of Consciousness (35/5 | 63/64)",
        },
        "pin": {
            "defined_centers": {"Heart", "Root", "Sacral", "SolarPlexus",
                                "Spleen", "Throat"},
        },
    },
    {
        # Buzz Aldrin.
        # Born 20 January 1930, 14:17 EST (UTC-5), Glen Ridge, NJ — Rodden AA
        # (Astro-Databank).  14:17 -> 19:17 UT.
        # Chart values: cited as the canonical 4/1 "Splenic Manifestor" in
        # loveyourhumandesign.com "Manifestors Among Us" and listed as a
        # notable 4/1 (Juxtaposition) profile by nicolelaino.com and
        # humandesignhd.com.  The 4/1 profile is by definition the only
        # Juxtaposition angle.
        "name": "Buzz Aldrin",
        "coverage": "Manifestor / Splenic / JUXTAPOSITION 4-1 / defined Head",
        "birth": dict(year=1930, month=1, day=20, hour_ut=19 + 17 / 60,
                      lat=40.8026, lon=-74.2043),
        "expect": {
            "type": "Manifestor",
            "authority": "Splenic",
            "profile": "4/1",
            "cross_prefix": "Juxtaposition",
        },
        "pin": {
            "definition": "Single Definition",
            "cross": "Juxtaposition Cross of Limitation (60/56 | 28/27)",
            "defined_centers": {"Ajna", "Head", "Root", "Spleen", "Throat"},
            "head_defined": True,
        },
    },
    {
        # Uri Geller.
        # Born 20 December 1946, 02:00, Tel Aviv (UTC+2, Palestine winter
        # time — DST ended before December) — Astro-Databank, Rodden A
        # (time via Puharich).  02:00 +2h -> 00:00 UT same day.
        # Chart values: listed as a famous REFLECTOR by multiple independent
        # HD sources (freehumandesignchart.com, omapadotesouro.com,
        # thehumblewarrior.co.uk, amberclements.com).  Reflector implies
        # Lunar authority, No Definition and zero defined centers.
        # Note: a minority of sources give 02:30; the engine yields an
        # identical Reflector chart at both times.
        # Only the Reflector-derived fields are asserted (profile/cross not
        # published by the sources).
        "name": "Uri Geller",
        "coverage": "REFLECTOR / Lunar / No Definition (zero centers)",
        "birth": dict(year=1946, month=12, day=20, hour_ut=0.0,
                      lat=32.0853, lon=34.7818),
        "expect": {
            "type": "Reflector",
            "authority": "Lunar",
            "definition": "No Definition",
            "defined_centers": set(),
        },
        "pin": {},
    },
]

# ---------------------------------------------------------------------------
# Machinery
# ---------------------------------------------------------------------------
_CHART_CACHE: dict = {}


def get_chart(fx):
    key = fx["name"]
    if key not in _CHART_CACHE:
        _CHART_CACHE[key] = compute_hd_chart(**fx["birth"])
    return _CHART_CACHE[key]


def _assert_fields(fx, fields, tier):
    chart = get_chart(fx)
    name = fx["name"]
    for field, want in fields.items():
        if field == "type":
            got = chart.type_
        elif field == "authority":
            got = chart.authority
        elif field == "profile":
            got = chart.profile
        elif field == "definition":
            got = chart.definition
        elif field == "cross":
            got = chart.incarnation_cross
        elif field == "cross_prefix":
            got = chart.incarnation_cross
            assert got.startswith(want), (
                f"{name} [{tier}] cross {got!r} does not start with {want!r}"
            )
            continue
        elif field == "defined_centers":
            got = chart.defined_centers
        elif field == "head_defined":
            got = "Head" in chart.defined_centers
        elif field == "undefined_contains":
            missing = want - chart.undefined_centers
            assert not missing, (
                f"{name} [{tier}] expected undefined centers {sorted(want)}, "
                f"but {sorted(missing)} are defined"
            )
            continue
        else:
            raise ValueError(f"unknown fixture field {field!r}")
        assert got == want, (
            f"{name} [{tier}] {field}: got {got!r}, expected {want!r}"
        )


def make_expected_test(fx):
    def test():
        _assert_fields(fx, fx["expect"], "sourced")
    test.__name__ = f"test_expected_{fx['name'].lower().replace(' ', '_')}"
    return test


def make_pin_test(fx):
    def test():
        _assert_fields(fx, fx["pin"], "pin")
    test.__name__ = f"test_pins_{fx['name'].lower().replace(' ', '_')}"
    return test


def make_invariant_test(fx):
    def test():
        check_chart(get_chart(fx))
    test.__name__ = f"test_invariants_{fx['name'].lower().replace(' ', '_')}"
    return test


def test_suite_coverage():
    """The fixture set as a whole must cover the required matrix."""
    charts = [get_chart(fx) for fx in FIXTURES]
    types = {c.type_ for c in charts}
    for t in ("Projector", "Manifestor", "ManifestingGenerator", "Reflector"):
        assert t in types, f"suite is missing a {t} fixture"
    auths = {c.authority for c in charts}
    for a in ("Sacral", "Splenic", "Lunar"):
        assert a in auths, f"suite is missing {a} authority"
    defs = {c.definition for c in charts}
    assert "Single Definition" in defs and "Split Definition" in defs, (
        f"suite is missing Single/Split definition coverage: {defs}"
    )
    assert any("Head" in c.defined_centers for c in charts), (
        "suite has no chart with a defined Head center"
    )
    assert any(c.incarnation_cross.startswith("Left Angle") for c in charts), (
        "suite has no Left Angle cross"
    )
    assert any(c.incarnation_cross.startswith("Juxtaposition") for c in charts), (
        "suite has no Juxtaposition (4/1) fixture"
    )


# ---------------------------------------------------------------------------
# Self-runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import traceback

    tests = [check_tables]
    for fx in FIXTURES:
        tests.append(make_expected_test(fx))
        if fx["pin"]:
            tests.append(make_pin_test(fx))
        tests.append(make_invariant_test(fx))
    tests.append(test_suite_coverage)

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
