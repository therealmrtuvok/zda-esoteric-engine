"""
Tests for the interpretation layer.

These do not check that the copy is *good* — that is an editorial judgement.
They check the layer is complete and safe: every value the engine can emit has
text attached, nothing is silently blank, and interpretation never alters a
calculated chart.
"""

import sys, os
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TESTS_DIR))
sys.path.insert(0, TESTS_DIR)

import copy
from src.interpretations import (
    TYPES, AUTHORITIES, LINES, CENTERS, LIFE_PATHS, PERSONAL_YEARS,
    interpret_chart, interpret_human_design, interpret_numerology,
)
from src.hd_tables import CENTERS as ENGINE_CENTERS
from src.human_design import compute_hd_chart, hd_chart_to_dict
from src.numerology import numerology_report
from invariants import VALID_TYPES, VALID_PROFILES, AUTHORITY_EXPECT
from datetime import date


def test_every_type_has_copy():
    """Each of the five types the engine can return must be covered."""
    keys = {k.replace(" ", "") for k in TYPES}
    for t in VALID_TYPES:
        assert t.replace(" ", "") in keys, f"no interpretation for type {t!r}"


def test_every_authority_has_copy():
    labels = {label for _c, label in AUTHORITY_EXPECT} | {"Mental / None", "Lunar"}
    for label in labels:
        assert label in AUTHORITIES, f"no interpretation for authority {label!r}"


def test_every_profile_line_has_copy():
    lines = {n for pair in VALID_PROFILES for n in pair}
    for n in lines:
        assert n in LINES, f"no interpretation for profile line {n}"


def test_every_center_has_copy():
    for c in ENGINE_CENTERS:
        assert c in CENTERS, f"no interpretation for centre {c!r}"
    assert set(CENTERS) == set(ENGINE_CENTERS), "centre names drifted from the engine"


def test_every_life_path_has_copy():
    for n in list(range(1, 10)) + [11, 22, 33]:
        assert n in LIFE_PATHS, f"no interpretation for life path {n}"
    for n in range(1, 10):
        assert n in PERSONAL_YEARS, f"no interpretation for personal year {n}"


def test_no_blank_strings():
    """A missing string is worse than a missing key — it renders as emptiness."""
    def check(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check(v, f"{path}.{k}")
        elif isinstance(obj, (tuple, list)):
            for i, v in enumerate(obj):
                check(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            assert obj.strip(), f"blank interpretation string at {path}"
    for name, table in (("TYPES", TYPES), ("AUTHORITIES", AUTHORITIES),
                        ("LINES", LINES), ("CENTERS", CENTERS),
                        ("LIFE_PATHS", LIFE_PATHS), ("PERSONAL_YEARS", PERSONAL_YEARS)):
        check(table, name)


def test_real_chart_is_fully_interpreted():
    """A real computed chart must come back with no empty interpretation slots."""
    hd = hd_chart_to_dict(compute_hd_chart(1961, 8, 5, 5 + 24/60, 21.3069, -157.8583))
    num = numerology_report(date(1961, 8, 4), date(2026, 7, 19))
    out = interpret_chart(human_design=hd, numerology=num)

    t = out["human_design"]["type"]
    assert t["name"] and t.get("summary") and t.get("strategy")
    a = out["human_design"]["authority"]
    assert a["name"] and a.get("summary")
    assert len(out["human_design"]["profile"]["lines"]) == 2
    assert len(out["human_design"]["centers"]) == 9
    for c in out["human_design"]["centers"]:
        assert c["text"], f"centre {c['center']} has no text"
    assert out["numerology"]["life_path"]["name"]
    assert out["numerology"]["personal_year"]["text"]


def test_defined_flag_matches_the_chart():
    hd = hd_chart_to_dict(compute_hd_chart(1961, 8, 5, 5 + 24/60, 21.3069, -157.8583))
    out = interpret_human_design(hd)
    defined = {c["center"] for c in out["centers"] if c["defined"]}
    assert defined == set(hd["defined_centers"]), (
        f"interpretation defined set {sorted(defined)} ≠ chart {sorted(hd['defined_centers'])}"
    )


def test_interpretation_never_mutates_the_chart():
    """The layer must be read-only with respect to calculated data."""
    hd = hd_chart_to_dict(compute_hd_chart(1961, 8, 5, 5 + 24/60, 21.3069, -157.8583))
    num = numerology_report(date(1961, 8, 4), date(2026, 7, 19))
    hd_before, num_before = copy.deepcopy(hd), copy.deepcopy(num)
    interpret_chart(human_design=hd, numerology=num)
    assert hd == hd_before, "interpretation mutated the Human Design chart"
    assert num == num_before, "interpretation mutated the numerology result"


def test_handles_unknown_values_gracefully():
    """Bad input must not raise — a missing interpretation is not a crash."""
    out = interpret_human_design({"type": "Nonexistent", "authority": "Made Up",
                                  "profile": "9/9", "defined_centers": []})
    assert out["type"]["name"] == "Nonexistent"
    assert out["profile"]["lines"] == []
    assert len(out["centers"]) == 9
    assert interpret_numerology({})["life_path"]["number"] is None


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}"); passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}"); traceback.print_exc(); failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
