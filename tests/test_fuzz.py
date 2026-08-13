"""
Addendum 3 — Part 4: fuzz harness.
Generates N random valid birth inputs (1920-2030, random lat/lon) and asserts
every Part-2 invariant on each. Seeded, so failures are reproducible.

  python3 tests/test_fuzz.py            # N=1000 (CI gate)
  FUZZ_N=100 python3 tests/test_fuzz.py # quicker local run
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.human_design import compute_hd_chart
from invariants import check_chart, check_tables

SEED = 20260719
N = int(os.environ.get("FUZZ_N", "1000"))


def random_input(rng: random.Random) -> dict:
    year = rng.randint(1920, 2030)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)          # valid in every month
    hour_ut = rng.uniform(0, 24)
    lat = rng.uniform(-66, 66)        # avoid polar-circle house failures
    lon = rng.uniform(-180, 180)
    return dict(year=year, month=month, day=day, hour_ut=hour_ut,
                lat=lat, lon=lon)


def run_fuzz(n: int = N, seed: int = SEED) -> dict:
    check_tables()
    rng = random.Random(seed)
    type_counts: dict[str, int] = {}
    failures = []

    for i in range(n):
        inp = random_input(rng)
        try:
            chart = compute_hd_chart(**inp)
            check_chart(chart)
            type_counts[chart.type_] = type_counts.get(chart.type_, 0) + 1
        except AssertionError as e:
            failures.append((i, inp, str(e)))
            if len(failures) >= 5:
                break
        except Exception as e:
            failures.append((i, inp, f"{type(e).__name__}: {e}"))
            if len(failures) >= 5:
                break

    return {"n": n, "type_counts": type_counts, "failures": failures}


if __name__ == "__main__":
    print(f"fuzzing {N} random charts (seed {SEED})…")
    result = run_fuzz()
    for t, c in sorted(result["type_counts"].items(), key=lambda x: -x[1]):
        print(f"  {t:<22} {c}")
    if result["failures"]:
        print(f"\n{len(result['failures'])} FAILURES (showing first 5):")
        for i, inp, msg in result["failures"]:
            print(f"  #{i}: {inp}")
            print(f"      {msg}")
        sys.exit(1)
    checked = sum(result["type_counts"].values())
    print(f"\nall invariants hold on {checked}/{N} random charts")
    sys.exit(0)
