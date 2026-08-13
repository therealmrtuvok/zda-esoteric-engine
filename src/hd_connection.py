"""
Human Design connection (partnership) chart.
Runs two people's Personality+Design activations through the channel mapper
together and classifies how each composite channel is made.
"""

from .human_design import HdChart, _activations_from_positions
from .hd_tables import CHANNELS, GATE_CENTER, CENTERS, determine_definition
from .ephemeris_core import calc_at_jd


def _person_gates(chart: HdChart) -> set[int]:
    return set(chart.all_gates)


def _has_full_channel(gates: set[int], ga: int, gb: int) -> bool:
    return ga in gates and gb in gates


def connection_chart(chart_a: HdChart, chart_b: HdChart) -> dict:
    """
    Combine two charts. For every channel whose two gates are activated
    across the pair, classify the connection:
      - companionship: both people have the full channel themselves
      - dominance:     one has the full channel, the other has neither gate
      - compromise:    one has the full channel, the other has only one gate
      - electromagnetic: each brings one gate (neither has the channel alone)
    """
    ga_set = _person_gates(chart_a)
    gb_set = _person_gates(chart_b)
    union = ga_set | gb_set

    channels = []
    defined_channels = set()
    for c_ga, c_gb in CHANNELS:
        if c_ga not in union or c_gb not in union:
            continue
        defined_channels.add((min(c_ga, c_gb), max(c_ga, c_gb)))

        a_full = _has_full_channel(ga_set, c_ga, c_gb)
        b_full = _has_full_channel(gb_set, c_ga, c_gb)
        a_partial = (c_ga in ga_set) or (c_gb in ga_set)
        b_partial = (c_ga in gb_set) or (c_gb in gb_set)

        if a_full and b_full:
            kind = "companionship"
        elif a_full or b_full:
            kind = "compromise" if (a_partial and b_partial) else "dominance"
        else:
            kind = "electromagnetic"

        channels.append({
            "channel": (min(c_ga, c_gb), max(c_ga, c_gb)),
            "centers": (GATE_CENTER[c_ga], GATE_CENTER[c_gb]),
            "kind": kind,
        })

    # Centers defined by the composite channels
    defined_centers = set()
    for ch in defined_channels:
        defined_centers.add(GATE_CENTER[ch[0]])
        defined_centers.add(GATE_CENTER[ch[1]])

    definition, components = determine_definition(defined_centers, defined_channels)

    # Which centers are newly defined by the pairing (neither has solo)
    newly_defined = defined_centers - (chart_a.defined_centers | chart_b.defined_centers)

    return {
        "channels": channels,
        "defined_centers": sorted(defined_centers),
        "undefined_centers": sorted(set(CENTERS) - defined_centers),
        "newly_defined_centers": sorted(newly_defined),
        "definition": definition,
        "electromagnetic": [c["channel"] for c in channels if c["kind"] == "electromagnetic"],
        "companionship":   [c["channel"] for c in channels if c["kind"] == "companionship"],
        "dominance":       [c["channel"] for c in channels if c["kind"] == "dominance"],
        "compromise":      [c["channel"] for c in channels if c["kind"] == "compromise"],
    }


def hd_transit_overlay(natal_chart: HdChart, transit_jd: float) -> dict:
    """
    Current transiting activations overlaid on a natal bodygraph:
    which gates are lit right now, and which channels/centers become
    temporarily defined by natal+transit gates together.
    """
    transiting = calc_at_jd(transit_jd)
    t_acts = _activations_from_positions(transiting)
    t_gates = {a.gate for a in t_acts.values()}

    union = natal_chart.all_gates | t_gates
    active_channels = {
        (min(a, b), max(a, b))
        for a, b in CHANNELS
        if a in union and b in union
    }
    new_channels = active_channels - natal_chart.defined_channels

    active_centers = set()
    for ch in active_channels:
        active_centers.add(GATE_CENTER[ch[0]])
        active_centers.add(GATE_CENTER[ch[1]])
    new_centers = active_centers - natal_chart.defined_centers

    return {
        "transit_gates": sorted(t_gates),
        "transit_activations": {p: {"gate": a.gate, "line": a.line}
                                for p, a in t_acts.items()},
        "new_channels": sorted(new_channels),
        "new_centers": sorted(new_centers),
        "all_active_channels": sorted(active_channels),
        "all_active_centers": sorted(active_centers),
    }
