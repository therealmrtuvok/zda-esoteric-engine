#!/usr/bin/env python3
"""
Full natal report for one person: astrology, Human Design and numerology.

Usage:
  python tools/natal_report.py --name Sylvia --birth 1986-05-21 --time 12:42 \
      --tz -4 --lat 43.6532 --lon -79.3832 --place "Toronto, Canada"

--tz is the offset from UTC in force AT THE BIRTH MOMENT, not the zone's
standard offset. Two that bite:
  South Korea observed daylight saving in 1987 and 1988, so summer births
  there are UTC+10, not +9.
  North American summer births are daylight time, so Toronto in May is -4.

Nothing here is written to disk. Birth data belongs to the person it describes.
"""

import argparse
import sys
from datetime import date

sys.path.insert(0, ".")

from src.ephemeris_core import calc_chart
from src.human_design import compute_hd_chart
from src.astrology import (longitude_to_sign_degree, whole_sign_house,
                           placidus_house, get_aspects)
from src.hd_tables import longitude_to_activation, GATE_CENTER, GATE_CHANNEL_PARTNERS
from src.gate_names import GATE_NAMES
from src.hd_structure import islands
from src.numerology import life_path, numerology_report

ELEMENT = {"Aries":"fire","Leo":"fire","Sagittarius":"fire",
           "Taurus":"earth","Virgo":"earth","Capricorn":"earth",
           "Gemini":"air","Libra":"air","Aquarius":"air",
           "Cancer":"water","Scorpio":"water","Pisces":"water"}
MODE = {"Aries":"cardinal","Cancer":"cardinal","Libra":"cardinal","Capricorn":"cardinal",
        "Taurus":"fixed","Leo":"fixed","Scorpio":"fixed","Aquarius":"fixed",
        "Gemini":"mutable","Virgo":"mutable","Sagittarius":"mutable","Pisces":"mutable"}
CLASSICAL = ["sun","moon","mercury","venus","mars","jupiter","saturn"]
ORDER = CLASSICAL + ["uranus","neptune","pluto","true_node","chiron","juno"]


def report(name, birth, hour_ut, lat, lon, place, tz):
    ch = calc_chart(birth.year, birth.month, birth.day, hour_ut, lat, lon)
    hd = compute_hd_chart(birth.year, birth.month, birth.day, hour_ut, lat, lon)

    asc_s, asc_d = longitude_to_sign_degree(ch.ascendant)
    mc_s, mc_d = longitude_to_sign_degree(ch.mc)
    sun_s, sun_d = longitude_to_sign_degree(ch.planets["sun"].longitude)
    mo_s, mo_d = longitude_to_sign_degree(ch.planets["moon"].longitude)

    print("=" * 66)
    print(f"{name.upper()}   {birth.isoformat()}  {place}   UTC{tz:+g}")
    print("=" * 66)
    # Degrees within a sign run 0 to 29.99, so rounding 29.79 up to 30 prints
    # a degree that does not exist. Truncate, and show the minutes.
    def deg(x):
        return f"{int(x)}\u00b0{int(round((x % 1) * 60)):02d}'"
    print(f"\n  Sun {deg(sun_d)} {sun_s}   Moon {deg(mo_d)} {mo_s}   "
          f"Rising {deg(asc_d)} {asc_s}   MC {deg(mc_d)} {mc_s}\n")

    print("  PLACEMENTS")
    print(f"  {'planet':<11}{'position':<22}{'whole':<7}{'placidus'}")
    el, md = {}, {}
    for n in ORDER:
        p = ch.planets.get(n)
        if not p:
            continue
        s, d = longitude_to_sign_degree(p.longitude)
        rx = "Rx" if p.retrograde else ""
        print(f"  {n:<11}{d:>6.2f} {s:<12}{rx:<3}"
              f"{whole_sign_house(p.longitude, ch.ascendant):^7}"
              f"{placidus_house(p.longitude, ch.houses_placidus):^8}")
        if n in CLASSICAL:
            el[ELEMENT[s]] = el.get(ELEMENT[s], 0) + 1
            md[MODE[s]] = md.get(MODE[s], 0) + 1
    print(f"\n  elements (7 classical): "
          + ", ".join(f"{k} {v}" for k, v in sorted(el.items(), key=lambda x: -x[1])))
    print(f"  modes                 : "
          + ", ".join(f"{k} {v}" for k, v in sorted(md.items(), key=lambda x: -x[1])))

    print("\n  TIGHTEST ASPECTS")
    major = {"Conjunction", "Opposition", "Trine", "Square", "Sextile"}
    rows = sorted([a for a in get_aspects(ch) if a["aspect"] in major],
                  key=lambda a: a["orb"])
    for a in rows[:10]:
        print(f"    {a['planet_a']:<10}{a['symbol']} {a['planet_b']:<11}"
              f"{a['aspect']:<12} orb {a['orb']:>5.2f}")

    print(f"\n  HUMAN DESIGN")
    print(f"    {hd.type_}, {hd.authority} authority, profile {hd.profile}, "
          f"{hd.definition}")
    print(f"    strategy: {hd.strategy}   not-self: {hd.not_self_theme}")
    print(f"    cross: {hd.incarnation_cross}")
    print(f"    defined: {', '.join(sorted(hd.defined_centers)) or 'none'}")
    print(f"    open   : {', '.join(sorted(hd.undefined_centers)) or 'none'}")
    print(f"    channels: {', '.join(f'{a}-{b}' for a,b in sorted(hd.defined_channels)) or 'none'}")
    isl = islands(hd)
    if len(isl) > 1:
        for i in isl:
            print(f"      island {i['index']}: {' + '.join(i['centers'])}")
    hang = [g for g in sorted(hd.all_gates)
            if any(p not in hd.all_gates for p in GATE_CHANNEL_PARTNERS[g])]
    print(f"    hanging gates ({len(hang)}): {hang}")

    num = numerology_report(birth, date.today())
    print(f"\n  NUMEROLOGY")
    print(f"    life path {num['life_path']}   "
          f"personal year {num['personal_year']} (today)")
    print()
    return ch, hd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--birth", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM local clock time")
    ap.add_argument("--tz", required=True, type=float,
                    help="UTC offset in force at birth, e.g. -4 for EDT")
    ap.add_argument("--lat", required=True, type=float)
    ap.add_argument("--lon", required=True, type=float, help="east positive")
    ap.add_argument("--place", default="")
    a = ap.parse_args()
    hh, mm = (int(x) for x in a.time.split(":"))
    report(a.name, date.fromisoformat(a.birth), hh + mm / 60 - a.tz,
           a.lat, a.lon, a.place, a.tz)


if __name__ == "__main__":
    main()
