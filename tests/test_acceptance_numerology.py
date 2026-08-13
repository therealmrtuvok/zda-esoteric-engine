"""
Acceptance test — numerology layer.
Reference chart: Barack Obama, born 4 August 1961 (see test_acceptance_astrology).

Life Path 2 is the externally checkable value here — it is widely published for
this birth date and is reproducible by hand: 8 + 4 + (1+9+6+1=17→8) = 20 → 2.

The personal year runs birthday to birthday, based on the calendar year of the
MOST RECENT birthday — not the current calendar year. That convention is the
behaviour under test at the 3 August / 4 August boundary below.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from src.numerology import life_path, personal_year, numerology_report

BIRTH = date(1961, 8, 4)


def test_life_path():
    # 8, 4, 1961→17→8; 8+4+8=20→2  (published value for this birth date)
    assert life_path(BIRTH) == 2


def test_personal_year_before_birthday():
    # July 2026: last birthday 4 Aug 2025 → 8+4+(2025→9)=21→3
    assert personal_year(BIRTH, date(2026, 7, 19)) == 3


def test_personal_year_on_birthday():
    # 4 Aug 2026: 2026→10→1; 8+4+1=13→4
    assert personal_year(BIRTH, date(2026, 8, 4)) == 4


def test_personal_year_day_before_birthday():
    assert personal_year(BIRTH, date(2026, 8, 3)) == 3


def test_personal_year_after_birthday():
    assert personal_year(BIRTH, date(2026, 12, 31)) == 4


def test_report_shape():
    rep = numerology_report(BIRTH, date(2026, 7, 19))
    assert rep == {"life_path": 2, "personal_year": 3,
                   "personal_month": 1, "personal_day": 2}


if __name__ == "__main__":
    tests = [test_life_path, test_personal_year_before_birthday,
             test_personal_year_on_birthday, test_personal_year_day_before_birthday,
             test_personal_year_after_birthday, test_report_shape]
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
