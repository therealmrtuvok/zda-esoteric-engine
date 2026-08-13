"""
Acceptance test — numerology layer.
Reference chart. The personal year runs birthday to birthday,
based on the calendar year of the MOST RECENT birthday — not the current
calendar year. Independently confirmed: personal year 8 in July 2026, turning 9
on Oct 16 2026.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from src.numerology import life_path, personal_year, numerology_report

BIRTH = date(1994, 10, 16)


def test_life_path():
    # 10→1, 16→7, 1994→23→5; 1+7+5=13→4
    assert life_path(BIRTH) == 4


def test_personal_year_before_birthday():
    # July 2026: last birthday Oct 16 2025 → 1+7+9=17→8
    assert personal_year(BIRTH, date(2026, 7, 19)) == 8


def test_personal_year_on_birthday():
    # Oct 16 2026: 2026→10→1; 1+7+1=9
    assert personal_year(BIRTH, date(2026, 10, 16)) == 9


def test_personal_year_day_before_birthday():
    assert personal_year(BIRTH, date(2026, 10, 15)) == 8


def test_personal_year_after_birthday():
    assert personal_year(BIRTH, date(2026, 12, 31)) == 9


def test_report_shape():
    rep = numerology_report(BIRTH, date(2026, 7, 19))
    assert rep == {"life_path": 4, "personal_year": 8,
                   "personal_month": 6, "personal_day": 7}


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
