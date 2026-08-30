#!/usr/bin/env python3
"""
Build an energy calendar dataset: Human Design transit windows, astrology
events and numerology cycles for one person over one date range.

Emits a single JSON file the calendar page reads. The day records are kept
lean and reference windows by id rather than embedding them, so a long range
stays a small file and the same window is described once.

Usage:
  python tools/build_calendar.py --birth 1961-08-04 --time 19:24 \
      --tz -10 --lat 21.3069 --lon -157.8583 \
      --start 2026-09-01 --end 2027-04-30 --out calendar-data.json

--tz is the offset from UTC in hours at the moment of birth, so summer time
matters. Getting it wrong moves the Ascendant about 15 degrees and can change
the Type, which is the single most common way to produce a confident wrong
chart with this engine.
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, ".")

from src.ephemeris_core import calc_chart, calc_at_jd, julian_day
from src.human_design import compute_hd_chart, hd_chart_to_dict
from src.interpretations import (interpret_human_design, interpret_cross,
                                 interpret_variable, LIFE_PATHS, PERSONAL_YEARS)
from src.hd_tables import (GATE_CHANNEL_PARTNERS, GATE_CENTER,
                           longitude_to_activation)
from src.hd_transit import scan_channel_windows, ALL_BODIES, _transit_gates
from src.hd_meanings import (describe_channel, GATE_MEANINGS,
                             CHANNEL_MEANINGS, channel_key)
from src.hd_structure import islands, classify_completion, bridge_gates
from src.gate_names import GATE_NAMES
from src.numerology import life_path
from src.numerology_meanings import day_numbers
from src.sky_events import (mundane_events, scan_aspect_windows,
                            natal_points_from_chart, sign_of, degree_in_sign)

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def hanging_gates(hd) -> list[dict]:
    """
    Gates the person carries whose channel partner they lack. These are the
    standing open questions a transit can answer, and they are the reason this
    calendar exists at all.
    """
    out = []
    for gate in sorted(hd.all_gates):
        missing = [p for p in GATE_CHANNEL_PARTNERS[gate]
                   if p not in hd.all_gates]
        if missing:
            # Completing a hanging gate does one of three things, and the
            # difference matters more than the channel's meaning. Reported per
            # partner because one gate can have more than one.
            effects = [{"partner": p, **classify_completion(hd, gate, p)}
                       for p in sorted(missing)]
            rank = {"bridge": 0, "opens": 1, "local": 2, "already": 3}
            effects.sort(key=lambda e: rank[e["effect"]])
            out.append({
                "gate": gate,
                "name": GATE_NAMES[gate],
                "center": GATE_CENTER[gate],
                "theme": GATE_MEANINGS[gate]["theme"],
                "hanging": GATE_MEANINGS[gate]["hanging"],
                "waiting_on": sorted(missing),
                "effect": effects[0]["effect"],
                "effects": effects,
            })
    return out


def _interpretation(hd, birth: date) -> dict:
    """
    Every explainable property of the chart, with its text, so the page can
    open a panel on any of them. Assembled here rather than in the template
    because the copy belongs in the engine, not in a script tag.
    """
    d = hd_chart_to_dict(hd)
    out = interpret_human_design(d)
    lp = life_path(birth)
    lp_name, lp_text = LIFE_PATHS.get(lp, ("", ""))
    out["cross"] = interpret_cross(d)
    out["variable"] = interpret_variable(d)
    out["life_path"] = {"number": lp, "name": lp_name, "text": lp_text}
    return out


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def build(birth: date, hour_ut: float, lat: float, lon: float,
          start: date, end: date, step_days: float = 0.5) -> dict:
    hd = compute_hd_chart(birth.year, birth.month, birth.day, hour_ut, lat, lon)
    natal = calc_chart(birth.year, birth.month, birth.day, hour_ut, lat, lon)

    jd_start = julian_day(start.year, start.month, start.day, 0)
    jd_end = julian_day(end.year, end.month, end.day, 23.99)
    total_days = (end - start).days + 1

    # --- Human Design: channels a transit completes that the natal chart lacks
    raw_windows = scan_channel_windows(hd, jd_start, jd_end,
                                       bodies=ALL_BODIES, step_days=step_days)
    hd_windows = []
    for i, w in enumerate(raw_windows):
        ga, gb = (int(x) for x in w["channel"].split("-"))
        held = ga if ga in hd.all_gates else (gb if gb in hd.all_gates else None)
        desc = describe_channel(ga, gb, held_gate=held)
        # A window carried only by the Moon lasts hours, not days. It is real
        # but it is not a plan, so it is tagged rather than dropped.
        planets = w["planets"]
        span = (date.fromisoformat(w["end"])
                - date.fromisoformat(w["start"])).days + 1
        # A slow body can hold a gate for years. Pluto sitting in gate 41 for
        # the whole range is a real definition, but it is a background
        # condition for the period, not an event on any given day. Reported
        # once as standing rather than as a window on all 242 days, otherwise
        # it marks every cell and hides the things that actually come and go.
        standing = span >= 0.8 * total_days
        struct = classify_completion(hd, ga, gb)
        hd_windows.append({
            "id": f"hd{i}",
            "effect": struct["effect"],
            "joins": struct["joins"],
            "structure_note": struct["note"],
            **desc,
            "start": w["start"],
            "end": w["end"],
            "span_days": span,
            "standing": standing,
            "planets": planets,
            "center_effect": w["center_effect"],
            "fleeting": planets == ["moon"],
            "ongoing_at_end": w.get("ongoing", False),
            "both_halves_supplied": held is None,
        })

    hanging = hanging_gates(hd)
    by_id = {w["id"]: w for w in hd_windows}

    # --- Astrology
    sky = mundane_events(jd_start, jd_end)
    aspect_windows = scan_aspect_windows(
        natal_points_from_chart(natal), jd_start, jd_end)
    for i, w in enumerate(aspect_windows):
        w["id"] = f"asp{i}"

    # --- Per-day records
    sky_by_date: dict[str, list] = {}
    for e in sky:
        sky_by_date.setdefault(e["date"], []).append(e)

    days = []
    prev_year_num = None
    for d in daterange(start, end):
        key = d.isoformat()
        jd_noon = julian_day(d.year, d.month, d.day, 12.0)
        sun_lon = calc_at_jd(jd_noon)["sun"]["longitude"]
        gate, line, *_ = longitude_to_activation(sun_lon)

        active = [w["id"] for w in hd_windows
                  if w["start"] <= key <= w["end"]]
        asp_active = [w["id"] for w in aspect_windows
                      if w["start"] <= key <= w["end"]]
        asp_exact = [w["id"] for w in aspect_windows if key in w["exact"]]

        nums = day_numbers(birth, d)
        # The personal year turns over on the birthday, not on 1 January, so
        # inside a range that spans a birthday it changes mid-calendar. That
        # is a real hinge and it should be marked, not left to be noticed.
        year_turns = (prev_year_num is not None
                      and nums["personal_year"] != prev_year_num)
        prev_year_num = nums["personal_year"]

        # Which gate each transiting body sits in at noon. Needed to draw the
        # Design Chart for any selected day, not just to find completions.
        t_acts = _transit_gates(jd_noon, ALL_BODIES)
        t_gates: dict[int, list[str]] = {}
        for body, act in t_acts.items():
            t_gates.setdefault(act["gate"], []).append(body)

        days.append({
            "date": key,
            "weekday": WEEKDAYS[d.weekday()],
            "personal_year_starts": year_turns,
            "transit_gates": {str(g): sorted(b) for g, b in sorted(t_gates.items())},
            **nums,
            "sun_gate": gate,
            "sun_line": line,
            "sun_gate_name": GATE_NAMES[gate],
            "sun_gate_theme": GATE_MEANINGS[gate]["theme"],
            "sun_sign": sign_of(sun_lon),
            "sun_degree": round(degree_in_sign(sun_lon), 2),
            "hd_windows": active,
            "aspects_active": asp_active,
            "aspects_exact": asp_exact,
            "sky": sky_by_date.get(key, []),
        })

    # How many days of the range each hanging gate is actually answered.
    # This turned out to be the only measure that discriminates: category
    # filters do not, because a handful of very long windows blanket the
    # calendar. A gate answered 6 days out of 249 and one answered 203 are
    # different situations and should not carry the same weight.
    coverage: dict[int, dict] = {}
    for rec in days:
        for wid in rec["hd_windows"]:
            w = by_id[wid]
            held = w.get("held_gate")
            if held is None:
                continue
            c = coverage.setdefault(held, {"solid": set(), "any": set()})
            c["any"].add(rec["date"])
            if not w["fleeting"]:
                c["solid"].add(rec["date"])

    total = len(days)
    for g in hanging:
        c = coverage.get(g["gate"], {"solid": set(), "any": set()})
        g["answered_days"] = len(c["solid"])
        g["answered_days_incl_moon"] = len(c["any"])
        g["answered_pct"] = round(len(c["solid"]) / total * 100, 1)

    pct_by_gate = {g["gate"]: g["answered_pct"] for g in hanging}
    for w in hd_windows:
        held = w.get("held_gate")
        w["scarcity_pct"] = pct_by_gate.get(held)
        # Rare means the gate this window answers is open for less than a
        # sixth of the range. Those are the dates worth planning around.
        w["rare"] = held is not None and pct_by_gate.get(held, 100) < 16

    return {
        "meta": {
            "generated_for_range": [start.isoformat(), end.isoformat()],
            "birth_date": birth.isoformat(),
            "days": len(days),
            "scan_step_days": step_days,
        },
        "chart": {
            "type": hd.type_,
            "profile": hd.profile,
            "authority": hd.authority,
            "definition": hd.definition,
            "life_path": life_path(birth),
            "defined_centers": sorted(hd.defined_centers),
            "defined_channels": [f"{a}-{b}" for a, b in
                                 sorted(hd.defined_channels)],
            "all_gates": sorted(hd.all_gates),
            "personality_gates": sorted({a.gate for a in hd.personality.values()}),
            "design_gates": sorted({a.gate for a in hd.design.values()}),
            "undefined_centers": sorted(hd.undefined_centers),
            "islands": islands(hd),
            "bridge_gates": {str(g): {**b, "name": GATE_NAMES[g],
                                      "theme": GATE_MEANINGS[g]["theme"]}
                             for g, b in sorted(bridge_gates(hd).items())},
            "incarnation_cross": hd.incarnation_cross,
            "strategy": hd.strategy,
            "not_self_theme": hd.not_self_theme,
            "variable": hd.variable,
        },
        # The full tables, so the Design Chart can describe any gate or channel
        # the reader clicks, not only the ones that happen to open in range.
        "meanings": {
            "channels": {f"{lo}-{hi}": describe_channel(lo, hi)
                         for lo, hi in sorted(CHANNEL_MEANINGS)},
            "gates": {str(g): {"name": GATE_NAMES[g],
                               "center": GATE_CENTER[g],
                               "partners": sorted(GATE_CHANNEL_PARTNERS[g]),
                               **GATE_MEANINGS[g]}
                      for g in range(1, 65)},
        },
        "interpretation": _interpretation(hd, birth),
        "hanging_gates": hanging,
        "standing_windows": [w for w in hd_windows if w["standing"]],
        "hd_windows": hd_windows,
        "aspect_windows": aspect_windows,
        "sky_events": sky,
        "days": days,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM local clock time")
    ap.add_argument("--tz", required=True, type=float,
                    help="offset from UTC in hours at birth, e.g. -4 for EDT")
    ap.add_argument("--lat", required=True, type=float)
    ap.add_argument("--lon", required=True, type=float,
                    help="east positive, west negative")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--step", type=float, default=0.5,
                    help="scan resolution in days")
    ap.add_argument("--out", default="calendar-data.json")
    ap.add_argument("--html", default=None,
                    help="also write a self-contained page with the data "
                         "inlined, so it opens by double-clicking rather than "
                         "needing a local server (fetch() is blocked on file://)")
    a = ap.parse_args()

    birth = date.fromisoformat(a.birth)
    hh, mm = (int(x) for x in a.time.split(":"))
    hour_ut = hh + mm / 60 - a.tz

    data = build(birth, hour_ut, a.lat, a.lon,
                 date.fromisoformat(a.start), date.fromisoformat(a.end),
                 step_days=a.step)

    payload = json.dumps(data, separators=(",", ":"))
    with open(a.out, "w") as f:
        f.write(payload)

    if a.html:
        tpl_path = os.path.join(os.path.dirname(__file__),
                                "calendar-template.html")
        with open(tpl_path) as f:
            tpl = f.read()
        token = "__CALENDAR_DATA__"
        if token not in tpl:
            raise SystemExit(f"{tpl_path} has no {token} placeholder")

        # The Design Chart SVG is generated by tools/gen_design_chart.py and is
        # pure geometry with id-addressable centres, gates and channel halves.
        # It is inlined rather than linked so the page stays one file.
        svg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "assets", "design-chart.svg")
        svg_token = "__DESIGN_CHART_SVG__"
        if svg_token in tpl:
            with open(svg_path) as f:
                tpl = tpl.replace(svg_token, f.read())
        # The payload goes inside a <script>. A literal "</script>" anywhere in
        # the data would close the tag early, so neutralise it. JSON escapes
        # the backslash back out on parse, so the data is unchanged.
        safe = payload.replace("</", "<\\/")
        with open(a.html, "w") as f:
            f.write(tpl.replace(token, safe))

    c = data["chart"]
    print(f"{c['type']}  {c['profile']}  {c['authority']} authority  "
          f"{c['definition']}  life path {c['life_path']}")
    print(f"defined channels: {len(c['defined_channels'])}   "
          f"hanging gates: {len(data['hanging_gates'])}")
    w = data["hd_windows"]
    print(f"HD windows: {len(w)}  "
          f"(moon-only: {sum(1 for x in w if x['fleeting'])}, "
          f"standing all period: {len(data['standing_windows'])}, "
          f"both halves from transit: {sum(1 for x in w if x['both_halves_supplied'])})")
    print(f"sky events: {len(data['sky_events'])}   "
          f"aspect windows: {len(data['aspect_windows'])}")
    print(f"wrote {a.out}  ({os.path.getsize(a.out)/1024:.0f} KB)")
    if a.html:
        print(f"wrote {a.html}  ({os.path.getsize(a.html)/1024:.0f} KB, "
              f"self-contained)")


if __name__ == "__main__":
    main()
