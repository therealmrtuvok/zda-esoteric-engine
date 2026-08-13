"""
Human Design transit overlays and future projection (addendum 2, parts A & B).
Merges three activation sources per gate — natal Personality, natal Design,
transit — and scans date ranges for transit-completed channel windows.
"""

from .ephemeris_core import calc_at_jd, jd_to_datetime_tuple
from .human_design import HdChart
from .hd_tables import (
    CHANNELS,
    GATE_CENTER,
    CENTERS,
    longitude_to_activation,
)

# The standard 13 HD transit bodies (earth / south_node derived from sun / node).
# Chiron/Juno are astrology-layer only and deliberately excluded — pass them
# explicitly in `bodies` if a non-standard overlay is ever wanted.
ALL_BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
              "uranus", "neptune", "pluto", "true_node"]

# Slow movers — default set for multi-year projections. Fast movers
# (Moon, Mercury, Venus, Sun, Mars) flicker channels on/off in hours-days.
SLOW_BODIES = ["jupiter", "saturn", "uranus", "neptune", "pluto", "true_node"]


def _transit_gates(jd: float, bodies: list[str]) -> dict[str, dict]:
    """
    Transiting activations for the chosen bodies at jd.
    Adds Earth if Sun is included and South Node if True Node is included.
    Returns {body: {"gate": g, "line": l}}.
    """
    positions = calc_at_jd(jd)
    lons = {b: positions[b]["longitude"] for b in bodies}
    if "sun" in bodies:
        lons["earth"] = (lons["sun"] + 180) % 360
    if "true_node" in bodies:
        lons["south_node"] = (lons["true_node"] + 180) % 360

    out = {}
    for body, lon in lons.items():
        gate, line, *_ = longitude_to_activation(lon)
        out[body] = {"gate": gate, "line": line}
    return out


def transit_state(natal: HdChart, transit_jd: float,
                  bodies: list[str] = None) -> dict:
    """
    Full merged state object for rendering:
      gates:    {gate: {"activated": bool, "sources": [...]}}
      channels: {"lo-hi": {"defined": bool, "by": [...], "transitCompleted": bool}}
      centersTransit: {center: bool}  — defined only WITH transits included
      centersNatal:   {center: bool}
    Sources are "personality" | "design" | "transit".
    """
    bodies = bodies or ALL_BODIES

    p_gates = {a.gate for a in natal.personality.values()}
    d_gates = {a.gate for a in natal.design.values()}
    t_acts = _transit_gates(transit_jd, bodies)
    t_gates = {a["gate"] for a in t_acts.values()}

    gates = {}
    for g in range(1, 65):
        sources = []
        if g in p_gates:
            sources.append("personality")
        if g in d_gates:
            sources.append("design")
        if g in t_gates:
            sources.append("transit")
        gates[g] = {"activated": bool(sources), "sources": sources}

    channels = {}
    centers_transit = set()
    for ga, gb in CHANNELS:
        lo, hi = min(ga, gb), max(ga, gb)
        key = f"{lo}-{hi}"
        a_src = gates[ga]["sources"]
        b_src = gates[gb]["sources"]
        defined = bool(a_src) and bool(b_src)

        natal_defined = (lo, hi) in natal.defined_channels
        by = sorted(set(a_src) | set(b_src)) if defined else []
        transit_completed = defined and not natal_defined

        channels[key] = {
            "defined": defined,
            "by": by,
            "transitCompleted": transit_completed,
        }
        if defined:
            centers_transit.add(GATE_CENTER[ga])
            centers_transit.add(GATE_CENTER[gb])

    return {
        "gates": gates,
        "channels": channels,
        "centersNatal": {c: (c in natal.defined_centers) for c in CENTERS},
        "centersTransit": {c: (c in centers_transit) for c in CENTERS},
        "transit_activations": t_acts,
        "bodies": bodies,
    }


# ---------------------------------------------------------------------------
# Part B — channel-activation timeline
# ---------------------------------------------------------------------------
def _jd_to_iso(jd: float) -> str:
    y, m, d, _h = jd_to_datetime_tuple(jd)
    return f"{y:04d}-{m:02d}-{d:02d}"


def _completed_channels_on(natal: HdChart, jd: float,
                            bodies: list[str]) -> dict[tuple, list[str]]:
    """
    Channels transit-completed at jd → list of transiting bodies supplying
    a gate the natal chart lacks.
    """
    t_acts = _transit_gates(jd, bodies)
    gate_suppliers: dict[int, list[str]] = {}
    for body, a in t_acts.items():
        gate_suppliers.setdefault(a["gate"], []).append(body)
    t_gates = set(gate_suppliers)

    union = natal.all_gates | t_gates
    out = {}
    for ga, gb in CHANNELS:
        lo, hi = min(ga, gb), max(ga, gb)
        if (lo, hi) in natal.defined_channels:
            continue
        if ga in union and gb in union:
            suppliers = []
            for g in (ga, gb):
                if g not in natal.all_gates and g in gate_suppliers:
                    suppliers.extend(gate_suppliers[g])
            if suppliers:            # transit genuinely supplies a missing half
                out[(lo, hi)] = sorted(set(suppliers))
    return out


def scan_channel_windows(natal: HdChart, jd_start: float, jd_end: float,
                          bodies: list[str] = None,
                          step_days: float = 1.0) -> list[dict]:
    """
    Step through [jd_start, jd_end] and record dated windows where a
    transit completes a natal channel:
      [{channel, planets, start, end, center_effect}, ...]
    Defaults to SLOW_BODIES — include fast movers only for short ranges.
    """
    bodies = bodies or SLOW_BODIES

    open_windows: dict[tuple, dict] = {}
    windows: list[dict] = []

    jd = jd_start
    while jd <= jd_end + 1e-9:
        active = _completed_channels_on(natal, jd, bodies)

        for ch, planets in active.items():
            if ch not in open_windows:
                new_centers = ({GATE_CENTER[ch[0]], GATE_CENTER[ch[1]]}
                               - natal.defined_centers)
                effect = ("defines " + " & ".join(sorted(new_centers))
                          if new_centers else "reinforces defined centers")
                open_windows[ch] = {
                    "channel": f"{ch[0]}-{ch[1]}",
                    "planets": planets,
                    "start_jd": jd,
                    "start": _jd_to_iso(jd),
                    "center_effect": effect,
                }
            else:
                for p in planets:
                    if p not in open_windows[ch]["planets"]:
                        open_windows[ch]["planets"].append(p)

        for ch in list(open_windows):
            if ch not in active:
                w = open_windows.pop(ch)
                w["end_jd"] = jd - step_days
                w["end"] = _jd_to_iso(jd - step_days)
                windows.append(w)

        jd += step_days

    for ch, w in open_windows.items():
        w["end_jd"] = jd_end
        w["end"] = _jd_to_iso(jd_end)
        w["ongoing"] = True
        windows.append(w)

    windows.sort(key=lambda w: w["start_jd"])
    return windows
