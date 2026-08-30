# Energy calendar

A personal calendar merging three layers over a date range: Human Design
transit windows, astrology events, and numerology cycles. Output is a single
self-contained HTML page with a journal.

## Build one

```bash
python tools/build_calendar.py \
  --birth 1961-08-04 --time 19:24 --tz -10 \
  --lat 21.3069 --lon -157.8583 \
  --start 2026-09-01 --end 2027-04-30 \
  --out calendar-data.json --html energy-calendar.html
```

Open `energy-calendar.html` by double-clicking it. The data is inlined at build
time because `fetch()` is blocked on `file://`, so the page needs no server.

**`--tz` is the offset from UTC at the moment of birth, not the zone's standard
offset.** August 4 in Honolulu is HST, so `-10`. Getting it wrong
moves the Ascendant about 15 degrees and can change the Type. This is the most
common way to produce a confident wrong chart with this engine.

Generated calendars contain birth data and are gitignored. Keep it that way.

## Two views

**Calendar.** Month grid, one cell per day, with a journal on each.

**Design Chart.** The bodygraph from `assets/design-chart.svg`, bound by
element id. Channels are drawn as two halves, one per gate, which is what lets
a hanging gate render as a stub and a transit visibly fill the missing half.
Personality is dark, Design is gold, transit is purple, matching the pips in
the calendar. Every gate, channel and centre is clickable, and every chart
property (Type, Profile, Authority, Definition, Cross, Variable, life path)
opens its explanation from `interpretations.py`.

The chart follows whichever day is selected, so it doubles as a dated transit
chart rather than only a natal one.

## What the three layers contribute

**Human Design.** `scan_channel_windows` walks the range and records every
window where a transiting body supplies a gate the natal chart lacks, closing
a channel. Each window is classified:

| Flag | Meaning |
|---|---|
| `held_gate` set | you carry one half, a transit supplied the other. The interesting case |
| `both_halves_supplied` | neither gate is yours. Weather passing through, not something of yours completing |
| `fleeting` | carried by the Moon alone, so it lasts hours. Real, but not a plan |
| `standing` | spans 80% or more of the range. A slow planet parked in a gate. Reported once in the rail, not on every day |

Independently of that, `hd_structure.py` classifies what completing the channel
does to the shape of the definition:

| Effect | Meaning |
|---|---|
| `bridge` | joins two previously separate islands |
| `opens` | defines a centre the chart does not otherwise have |
| `local` | both ends already sit in the same island, nothing changes structurally |

These two axes are independent. A window can bridge two islands using gates the
person does not carry, which still changes the shape of their definition. On a
four-island chart that is most windows.

### Scarcity is the discriminator

Category filters do not narrow a calendar. On the reference chart 90 of 113
non-Moon windows are bridges, and a handful of very long windows blanket every
day of the range, so filtering on `bridge` leaves 249 days of 249.

What does discriminate is how many days of the range each hanging gate is
actually answered. On that same chart it runs from 203 days down to 6, and
`rare` (under a sixth of the range) selects 81 days in 13 blocks. That is the
filter worth having, and the reason `answered_days` and `scarcity_pct` exist.

**Astrology.** Retrograde stations, eclipses, new and full moons, sign
ingresses, and transiting outer-planet aspects to natal points. Aspect windows
use a 1.5 degree orb rather than the natal table's 8, because an 8 degree Pluto
square lasts years and is not a calendar entry. Every exact pass inside a
window is dated separately, since a retrograde makes the same aspect exact more
than once.

**Numerology.** Personal year, month and day. The personal year runs birthday
to birthday, not calendar year.

## The design claim behind it

A hanging gate is a standing open question. It gets answered by a person who
carries the other half of the channel, or by a transit, and by nothing else.
Environment and place do not define a channel. So the calendar is not decorative:
for someone with a hanging gate they feel the lack of, it is the list of dates
the sky supplies the missing half.

The copy in `hd_meanings.py` names the cost as plainly as the gift, because the
energy is borrowed. Sizing a commitment to how you feel inside a window is the
predictable way to get hurt by one.

## Regenerating

The dataset is a build artefact, not a database. Rebuild it for a new range or
after editing any meaning table. The journal lives in the browser's
localStorage, keyed by birth date, so rebuilding the page does not lose entries
as long as the birth date is unchanged. Export to Markdown from the rail before
changing birth data.
