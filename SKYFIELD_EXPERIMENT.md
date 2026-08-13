# Skyfield ephemeris — parked side experiment

## Why this exists
The engine currently runs on **Swiss Ephemeris** (`pyswisseph`), which is dual-licensed:
free under **AGPL** (public network service ⇒ must publish the engine's source) or a
paid commercial licence from Astrodienst (~CHF 750 one-time).

**Current decision (2026-07-27): ship under AGPL.** The `esoteric-engine` repo goes
public; the ZDA platform layer (accounts, tiers, interpretation content, branding)
stays private and simply calls the engine's API. Nothing in the code changes.

This document parks the alternative: replacing Swiss Ephemeris with
**Skyfield (MIT) + NASA JPL data (public domain)** — free for commercial use with no
source-publication obligation, so the engine could become closed later without paying.

## Status: setup done, implementation not started
- [x] `skyfield` 1.54 installed
- [x] Data files downloaded to `ephe_jpl/` (gitignored — regenerate with the commands below)
      - `de440s.bsp` (32 MB) — planets, **1849–2150**
      - `chiron.bsp` (2 MB) — Chiron via JPL Horizons SPK
      - `juno.bsp` (2 MB) — Juno via JPL Horizons SPK
- [ ] Rewrite `src/ephemeris_core.py` against Skyfield
- [ ] Verify: all 89 named tests + `FUZZ_N=1000` must pass unchanged

## Re-downloading the data files
```bash
mkdir -p ephe_jpl && cd ephe_jpl
curl -sL -o de440s.bsp "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp"
# Chiron = 2060, Juno = 3 (Horizons returns base64 SPK inside JSON)
for pair in "2060:chiron" "3:juno"; do
  num="${pair%%:*}"; name="${pair##*:}"
  curl -s "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%27${num}%3B%27&EPHEM_TYPE=SPK&START_TIME=%271919-01-01%27&STOP_TIME=%272035-01-01%27&OBJ_DATA=NO" -o ${name}_spk.json
  python3 -c "
import json, base64
d = json.load(open('${name}_spk.json'))
open('${name}.bsp','wb').write(base64.b64decode(d['spk']))"
done
```

## The work remaining (est. 1–2 focused hours)
Only `src/ephemeris_core.py` changes — it is the single module that imports the
ephemeris. Everything downstream consumes `ChartData` / `calc_at_jd()` and is untouched.

| Piece | Difficulty | Notes |
|---|---|---|
| Planet longitudes + speeds | easy | `earth.at(t).observe(planet).ecliptic_latlon(epoch='date')`; speed via finite difference or `.velocity` |
| Chiron / Juno | easy | load the extra `.bsp` kernels the same way |
| True lunar node | medium | not built into Skyfield — derive from the Moon's orbital plane (cross product of position & velocity → ascending node longitude), or compute from mean node + correction |
| **Ascendant / MC / Placidus cusps** | **hard — the real work** | Swiss Ephemeris gave these free. Needs sidereal time → RAMC → spherical trig for Asc/MC, then the Placidus semi-arc iteration. Whole Sign is trivial once Asc is right. |

**Interface to preserve exactly** (10 functions + 2 dataclasses):
`Planet`, `ChartData`, `calc_chart`, `calc_at_jd`, `calc_chart_at_jd`, `julian_day`,
`jd_to_datetime_tuple`, `binary_search_body_longitude`, `find_next_crossing`,
`binary_search_sun_longitude`.

## Acceptance bar for the swap
The swap is only accepted when, with **zero changes to any test**:
- `tests/test_acceptance_astrology.py` — 8/8 (Asc 21°27′ Scorpio, MC 5°49′ Virgo to the arcminute)
- `tests/test_acceptance_hd.py` — 16/16
- `tests/test_acceptance_derived.py` — 15/15 (returns exact to <1′)
- `tests/test_acceptance_transit.py`, `test_crosses.py`, `test_invariants.py`, `test_fixtures.py`
- `FUZZ_N=1000 python3 tests/test_fuzz.py`

## Known trade-off
`de440s.bsp` covers **1849–2150**. Swiss Ephemeris handles a far wider range. Fine for
any living client; a wider JPL kernel (`de441`, ~3 GB) exists if historical charts are
ever needed.
