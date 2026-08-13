# ZDA Esoteric Engine

A calculation core for **astrology**, **Human Design**, and **numerology**, built on
the Swiss Ephemeris. One shared source of planetary positions; each system layers
on top of it.

Powers the chart tools at [zerodegreealchemy.com](https://zerodegreealchemy.com).

---

## Design principle

The astronomy is never the risk — it's exact. **Every bug lives in a mapping table.**
So the engine is validated against known-correct charts, and the rules are
independently re-implemented in the test suite so the engine cannot confirm its
own mistakes.

That discipline has caught four real defects, each of which produced a perfectly
plausible chart and each of which was invisible on the primary reference chart:

| Bug | Why it hid |
|---|---|
| Two missing integration channels (34 in the table, not 36) | the reference chart activates no Gate 10 |
| Chiron included in Human Design activations | HD uses exactly 13 points; the reference chart's Chiron completed nothing |
| Every 4/6 profile got an unnamed incarnation cross | the 88° arc spans 15.64 gate-widths, so 4/6 lands 16 gates back while reference tables assume 15 |
| Personal year computed from the calendar year | it should run birthday to birthday |

The 4/6 bug was found by the fuzz harness on its first run.

## Architecture

Only `ephemeris_core` ever touches the ephemeris. Everything else consumes its output.

```
src/
  ephemeris_core.py   positions, speeds, houses, Asc/MC, crossing searches
  astrology.py        signs, Whole Sign + Placidus houses, aspects
  hd_tables.py        Rave mandala gate wheel, 36 channels, centres
  human_design.py     Design date, activations, Type/Authority/Profile/Definition/Variable
  crosses.py          all 192 named incarnation crosses
  derived_charts.py   progressions, solar/lunar returns, profections, synastry, composite, transits
  hd_connection.py    partnership charts and transit overlays
  hd_transit.py       transit merge state + multi-year channel-activation timeline
  numerology.py       life path, personal year/month/day (no ephemeris)
tools/
  gen_bodygraph.py    generates an id-addressable BodyGraph SVG for data-bound rendering
```

## Verification

**89 named tests + a seeded 1,000-chart fuzz harness.**

- `tests/test_acceptance_*.py` — known-correct reference chart, asserted to the arcminute
- `tests/test_fixtures.py` — 7 public-figure charts, each cross-checked against two
  independent sources, spanning all five Types, every definition class, and the
  Reflector zero-centres edge
- `tests/invariants.py` — an **independent re-implementation** of the type, authority,
  and channel rules
- `tests/test_fuzz.py` — asserts every invariant across random valid births (1920–2030)

```bash
python tests/test_fuzz.py            # FUZZ_N=1000 by default
FUZZ_N=200 python tests/test_fuzz.py # quicker
```

The Dockerfile runs the entire suite as a **build gate** — a chart regression fails the
build rather than shipping.

## Running it

```bash
pip install -r requirements.txt
uvicorn api.main:app --port 8777
```

Then `http://localhost:8777/docs`.

### Example

```bash
curl -X POST http://localhost:8777/natal/human-design \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1994-10-16","birth_time":"09:57",
       "timezone":"America/Toronto","latitude":44.2333,"longitude":-76.5}'
```

Birth data accepts either an explicit `timezone_offset_hours`, or an IANA
`timezone` resolved server-side — so historical daylight saving is handled
correctly. Getting EDT vs EST wrong shifts the Ascendant by roughly 15°.

### Endpoints

`/natal/astrology` · `/natal/human-design` · `/numerology` · `/progressions` ·
`/solar-return` · `/lunar-return` · `/profection` · `/synastry` · `/connection` ·
`/transits` · `/transit-state` · `/projection` · `/health`

`/health` recomputes the reference chart on every call and reports its arcminute
error, so a bad deploy is loud rather than silently wrong.

## Ephemeris data

Main planets use the Swiss Ephemeris built-in **Moshier** analytical model —
accurate well within an arcminute over the supported range, and verified by the
test suite rather than assumed. Chiron and Juno **require** the `seas_18.se1`
asteroid file (bundled in `data/ephe/`); Moshier cannot compute asteroids.

`SKYFIELD_EXPERIMENT.md` documents a parked route to a fully permissive stack
(Skyfield + NASA JPL data) if the AGPL obligation ever becomes inconvenient.

## Licence

**GNU AGPL v3** — see [LICENSE](LICENSE).

This engine links against [Swiss Ephemeris](https://www.astro.com/swisseph/)
(`pyswisseph`), which is dual-licensed AGPL or commercial. This project takes the
AGPL option, which is why the source is published: running AGPL software as a
network service entitles its users to the source.

Bundled Swiss Ephemeris data files are distributed under the same terms. If you
want to use this in a closed-source product, buy a commercial Swiss Ephemeris
licence from Astrodienst, or swap the ephemeris layer per `SKYFIELD_EXPERIMENT.md`.
