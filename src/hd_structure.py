"""
Structural reading of a chart: what completing a given channel actually does
to the shape of the definition.

Definition is not one property, it is a count of disconnected islands. A chart
with eight defined centres in four islands behaves nothing like a chart with
eight defined centres in one, and the difference is invisible if you only look
at which centres are coloured in.

So a hanging gate is not automatically interesting. Completing one does one of
three things, and the difference matters more than the channel's meaning:

  bridge  joins two previously separate islands. Reduces fragmentation.
  opens   defines a centre that was undefined. Adds capacity you never have.
  local   both ends already sit in the same island. Nothing changes structurally.

The classification is computed by rebuilding the components with the candidate
channel added and comparing, rather than by special-casing. That way it stays
correct for any chart, including Reflectors, where there are no components to
bridge at all.
"""

from .hd_tables import CHANNELS, GATE_CENTER, GATE_CHANNEL_PARTNERS


def _components(centers: set[str], channels: set[tuple[int, int]]) -> list[set[str]]:
    """Connected components of `centers` under `channels`."""
    adj: dict[str, set[str]] = {c: set() for c in centers}
    for a, b in channels:
        ca, cb = GATE_CENTER[a], GATE_CENTER[b]
        if ca in adj and cb in adj:
            adj[ca].add(cb)
            adj[cb].add(ca)
    seen: set[str] = set()
    out: list[set[str]] = []
    for c in sorted(centers):
        if c in seen:
            continue
        stack, comp = [c], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            seen.add(x)
            stack.extend(adj[x] - comp)
        out.append(comp)
    return out


def islands(hd) -> list[dict]:
    """
    The chart's islands of definition, largest first, each with the channels
    that hold it together. Ordered deterministically so island numbers shown
    to a reader stay stable between runs.
    """
    comps = _components(set(hd.defined_centers), set(hd.defined_channels))
    comps.sort(key=lambda c: (-len(c), sorted(c)))
    out = []
    for i, comp in enumerate(comps, 1):
        chans = sorted((a, b) for a, b in hd.defined_channels
                       if GATE_CENTER[a] in comp and GATE_CENTER[b] in comp)
        out.append({
            "index": i,
            "centers": sorted(comp),
            "channels": [f"{a}-{b}" for a, b in chans],
        })
    return out


def _island_index(islands_list: list[dict], center: str):
    for isl in islands_list:
        if center in isl["centers"]:
            return isl["index"]
    return None


def classify_completion(hd, gate_a: int, gate_b: int) -> dict:
    """
    What completing the channel (gate_a, gate_b) would do to this chart.
    Returns {"effect", "joins", "defines", "note"}, where effect is
    "bridge" | "opens" | "local" | "already" and `joins` names the two island
    indices a bridge connects.
    """
    lo, hi = min(gate_a, gate_b), max(gate_a, gate_b)
    if (lo, hi) in hd.defined_channels:
        return {"effect": "already", "joins": None, "defines": None,
                "note": "Already defined in you. Not something you wait for."}

    isl = islands(hd)
    before = len(isl)
    centers_after = set(hd.defined_centers) | {GATE_CENTER[lo], GATE_CENTER[hi]}
    new_centers = sorted(centers_after - set(hd.defined_centers))
    after = len(_components(centers_after,
                            set(hd.defined_channels) | {(lo, hi)}))

    if new_centers:
        return {
            "effect": "opens",
            "joins": None,
            "defines": new_centers,
            "note": ("Defines " + " and ".join(new_centers) +
                     ", a centre you do not otherwise have. Capacity rather "
                     "than connection."),
        }
    if after < before:
        a = _island_index(isl, GATE_CENTER[lo])
        b = _island_index(isl, GATE_CENTER[hi])
        return {
            "effect": "bridge",
            "joins": sorted(x for x in (a, b) if x is not None),
            "defines": None,
            "note": (f"Joins island {a} to island {b}. Two parts of you that "
                     f"are permanently separate are connected while this runs."),
        }
    return {
        "effect": "local",
        "joins": None,
        "defines": None,
        "note": ("Both ends already sit in the same island, so nothing changes "
                 "structurally. The channel's own meaning still applies."),
    }


def bridge_gates(hd) -> dict[int, dict]:
    """
    Every gate the chart does NOT carry whose arrival would bridge two islands,
    mapped to what it bridges and which of your gates it completes. This is the
    concrete answer to what a split chart needs from other people.
    """
    out: dict[int, dict] = {}
    for gate in sorted(hd.all_gates):
        for partner in GATE_CHANNEL_PARTNERS[gate]:
            if partner in hd.all_gates:
                continue
            c = classify_completion(hd, gate, partner)
            if c["effect"] == "bridge":
                out[partner] = {
                    "completes_your_gate": gate,
                    "channel": f"{min(gate, partner)}-{max(gate, partner)}",
                    "joins": c["joins"],
                }
    return out
