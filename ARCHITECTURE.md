# ZDA Esoteric Engine — architecture handoff

Paste this into a new session before touching the engine.

**Repo:** `~/Documents/ZDA/Code/esoteric-engine`
**Public:** `github.com/therealmrtuvok/zda-esoteric-engine`
**Deployed:** `https://zda-esoteric-engine.fly.dev`
**Licence:** AGPL v3. Non-negotiable, see "Licence" below.

A calculation core for astrology, Human Design and numerology on one shared
source of planetary positions. Python + FastAPI. ~4,900 lines.

---

## The one architectural rule

**Only `src/ephemeris_core.py` imports `swisseph`. Nothing else. Ever.**

Every other module consumes its output. This is what makes the engine testable,
what makes the Skyfield escape hatch possible, and what keeps the AGPL surface
in one file.

## Design principle

The astronomy is never the risk, it is exact. **Every bug lives in a mapping
table.** So the rules are independently re-implemented in `tests/invariants.py`,
and the engine is validated against externally-sourced charts, so it cannot
confirm its own mistakes.

---

## Module map

```
src/
  ephemeris_core.py   positions, speeds, houses, Asc/MC, JD helpers, crossing search
  astrology.py        signs, Whole Sign + Placidus houses, aspects, formatting
  hd_tables.py        gate wheel, 36 channels, 9 centres, type/authority/definition rules
  human_design.py     Design date (88 deg solar arc), activations, full chart
  crosses.py          all 192 named incarnation crosses
  gate_names.py       64 classical I Ching hexagram names
  numerology.py       life path, personal year/month/day  (no ephemeris at all)
  derived_charts.py   progressions, solar/lunar returns, profections, synastry,
                      composite, transit-to-natal
  hd_connection.py    partnership charts + transit overlay
  hd_transit.py       transit merge state + multi-year channel-activation timeline
  interpretations.py  pure text tables. Reads finished output, never alters a chart.
  gate_names.py       classical I Ching hexagram names for all 64 gates
  sky_events.py       stations, lunations, eclipses, ingresses, transit-to-natal
                      aspect windows with every exact pass dated
  hd_meanings.py      copy for all 36 channels and all 64 gates, including the
                      hanging-gate frame. Centres are derived from hd_tables,
                      never restated
  numerology_meanings.py  personal month and personal day copy, master numbers
                      included
api/main.py           FastAPI. 14 endpoints + /health
tools/gen_design_chart.py   emits an id-addressable Design Chart SVG for data binding
tools/build_calendar.py     builds a personal energy calendar for a date range
tools/calendar-template.html  the calendar page, data inlined at build time
```

## Energy calendar

`tools/build_calendar.py` merges the three layers into one dataset and emits a
self-contained page. See `CALENDAR.md`.

The one thing to understand before touching it: a channel window is only
interesting when the person carries one gate and a transit supplies the other.
`hanging_gates()` computes the standing open questions, and each window records
`held_gate` and `supplied_gate` so the copy can name which half is theirs.
Windows where both halves come from transit are flagged `both_halves_supplied`
and are weather, not personal. Windows spanning most of the range are flagged
`standing` and reported once rather than on every day, because a slow planet
parked in a gate would otherwise mark all 242 cells.

## Key signatures

```python
from src.ephemeris_core import calc_chart, julian_day, find_next_crossing
from src.human_design import compute_hd_chart, hd_chart_to_dict
from src.hd_connection import connection_chart
from src.numerology import numerology_report

calc_chart(year, month, day, hour_ut, lat, lon)   -> ChartData
compute_hd_chart(year, month, day, hour_ut, lat, lon) -> HdChart
hd_chart_to_dict(chart)                           -> plain dict, JSON-safe
connection_chart(chart_a, chart_b)                -> composite channels + kinds
numerology_report(birth_date, on_date)            -> dict
find_next_crossing(body, target_lon, jd_from, jd_to) -> jd or None
```

### The gotcha that bites everyone

**`hour_ut` is UTC decimal hours, not local time.**

```python
# born 19:24 HST (UTC-10) in Honolulu, so 05:24 UT the next day
compute_hd_chart(1961, 8, 5, 5 + 24/60, 21.3069, -157.8583)
```

Getting EDT vs EST wrong shifts the Ascendant by roughly 15 degrees and can
change the Type. The API layer accepts an IANA `timezone` string and resolves
historical DST server-side; the Python layer does not, so convert yourself.

---

## The four bugs that already happened

Do not reintroduce these. Each produced a perfectly plausible chart, and each
was invisible on the primary reference chart.

| Bug | Why it hid |
|---|---|
| 34 channels in the table instead of 36 | reference chart activates no Gate 10 |
| Chiron included in HD activations | HD uses exactly 13 points; Chiron completed nothing on the reference chart |
| Every 4/6 profile got an unnamed cross | the 88 deg arc spans 15.64 gate-widths, so 4/6 lands 16 gates back while reference tables assume 15. Fixed by keying the lookup on (sun gate, angle), not the four-gate quartet |
| Personal year from the calendar year | it runs birthday to birthday, based on the year of the last birthday |

The 4/6 bug was found by the fuzz harness on its first run.

## Verification

**89 named tests + a seeded 1,000-chart fuzz harness.**

- `tests/test_acceptance_*.py` — reference chart is a public figure with Rodden
  AA data, so expected values come from outside this engine. Angles agree with
  two published charts to under an arcminute
- `tests/test_fixtures.py` — 7 double-sourced celebrity charts covering all five
  Types, every definition class, and the Reflector zero-centres edge
- `tests/invariants.py` — independent re-implementation of type, authority and
  channel rules
- `tests/test_fuzz.py` — asserts every invariant across random valid births

```bash
python tests/test_fuzz.py             # FUZZ_N=1000 by default
FUZZ_N=200 python tests/test_fuzz.py  # quicker
```

**The Dockerfile runs the whole suite as a build gate.** A chart regression fails
the build rather than shipping.

## Ephemeris data

Main planets use Swiss Ephemeris's built-in **Moshier** analytical model. No
planet `.se1` files bundled.

**Chiron and Juno require `data/ephe/seas_18.se1`** (bundled, 223 KB). Moshier
cannot compute asteroids. `EPHE_PATH` env var points at it; the Dockerfile sets
`ENV EPHE_PATH=/app/data/ephe`.

`/health` recomputes the reference chart on every call and reports its arcminute
error, so a bad deploy is loud rather than silently wrong.

## Build notes

- `pyswisseph` has C++ sources, so the image needs **`build-essential`**, not
  just `gcc`
- Do not add `TestClient` to the build gate; it drags in `httpx`. Call the
  endpoint functions directly

## Deploy

Fly.io, region yyz, `auto_stop_machines = "suspend"`, `min_machines_running = 0`.
API key lives in Fly secrets and in Supabase (`ENGINE_API_KEY`) for the portal's
`engine-proxy` edge function.

**Never put the key in a `VITE_` variable.** Vite compiles those into the browser
bundle. See DEPLOY.md.

## Licence

`pyswisseph` is dual-licensed AGPL or commercial. This project takes AGPL, which
is why the source is public: running AGPL software as a network service entitles
users to the source. The **engine repo is public; the platform layer**
(accounts, tiers, interpretation content) **stays private** and calls this API.

`SKYFIELD_EXPERIMENT.md` documents a parked route to a fully permissive stack
(Skyfield + NASA JPL) if that ever needs to change.

## House style, applies to code comments and copy alike

- **No em dashes. Anywhere.** Use a comma, a full stop, or a colon.
- **No Jovian Archive trademarks.** Say Alchemy Wheel and Design Chart. Gate
  names come from `gate_names.py`, which uses the classical I Ching hexagram
  names deliberately, not Jovian keynotes.
- Interpretation copy: describe mechanics, not destiny. No prediction, no
  flattery. Name the difficulty as plainly as the gift.
- No personal birth data in the public repo.
