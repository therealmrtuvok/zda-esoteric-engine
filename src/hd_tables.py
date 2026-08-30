"""
Human Design mapping tables.
These are the most risk-prone part of the engine — the acceptance test
validates every entry against a known-correct chart.
"""

# ---------------------------------------------------------------------------
# Gate wheel
# Gate 41 anchors at 302° (2° Aquarius, tropical).
# The 64 gates proceed in Alchemy Wheel order with increasing ecliptic longitude.
# Each gate spans exactly 5.625° (360° / 64).
# ---------------------------------------------------------------------------
GATE_ANCHOR_DEGREE = 302.0
GATE_WIDTH = 5.625        # degrees per gate
LINE_WIDTH = 0.9375       # degrees per line  (GATE_WIDTH / 6)
COLOR_WIDTH = 0.15625     # degrees per color (LINE_WIDTH / 6)
TONE_WIDTH = 0.026041667  # degrees per tone  (COLOR_WIDTH / 6)
BASE_WIDTH = 0.004340278  # degrees per base  (TONE_WIDTH / 6)

# Verified against: natal Sun 22°58′ Libra → Gate 32 line 3 (profile 3/5).
GATE_WHEEL = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42,  3,
    27, 24,  2, 23,  8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33,  7,  4, 29, 59, 40, 64, 47,  6, 46, 18, 48, 57, 32, 50,
    28, 44,  1, 43, 14, 34,  9,  5, 26, 11, 10, 58, 38, 54, 61, 60,
]

# Precompute gate → index for O(1) lookup
_GATE_TO_IDX = {gate: idx for idx, gate in enumerate(GATE_WHEEL)}


def longitude_to_activation(lon: float) -> tuple[int, int, int, int, int]:
    """
    Map ecliptic longitude to (gate, line, color, tone, base).
    All sub-values are 1-indexed (1–6).
    """
    offset = (lon - GATE_ANCHOR_DEGREE) % 360.0
    gate_idx = int(offset / GATE_WIDTH)
    gate = GATE_WHEEL[gate_idx]

    within_gate = offset - gate_idx * GATE_WIDTH
    line = int(within_gate / LINE_WIDTH) + 1

    within_line = within_gate - (line - 1) * LINE_WIDTH
    color = int(within_line / COLOR_WIDTH) + 1

    within_color = within_line - (color - 1) * COLOR_WIDTH
    tone = int(within_color / TONE_WIDTH) + 1

    within_tone = within_color - (tone - 1) * TONE_WIDTH
    base = min(int(within_tone / BASE_WIDTH) + 1, 6)  # clamp floating-point edge

    return gate, line, color, tone, base


def opposite_gate(gate: int) -> int:
    """Return the gate ~180° opposite (Earth to a given Sun gate)."""
    idx = _GATE_TO_IDX[gate]
    return GATE_WHEEL[(idx + 32) % 64]


# ---------------------------------------------------------------------------
# Centers
# ---------------------------------------------------------------------------
CENTERS = [
    "Head", "Ajna", "Throat", "G", "Heart", "Sacral", "SolarPlexus", "Spleen", "Root",
]

CENTER_GATES: dict[str, list[int]] = {
    "Head":        [64, 61, 63],
    "Ajna":        [47, 24,  4, 17, 11, 43],
    "Throat":      [ 8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62],
    "G":           [ 1,  2,  7, 10, 13, 15, 25, 46],
    "Heart":       [21, 26, 40, 51],
    "Sacral":      [ 3,  5,  9, 14, 27, 29, 34, 42, 59],
    "SolarPlexus": [ 6, 22, 30, 36, 37, 49, 55],
    "Spleen":      [18, 28, 32, 44, 48, 50, 57],
    "Root":        [19, 38, 39, 41, 52, 53, 54, 58, 60],
}

# Precompute gate → center
GATE_CENTER: dict[int, str] = {}
for _center, _gates in CENTER_GATES.items():
    for _g in _gates:
        GATE_CENTER[_g] = _center


# ---------------------------------------------------------------------------
# 36 Channels  (gate_a, gate_b)
# The integration-circuit gates (10, 20, 34, 57) each appear in multiple channels.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# The four quarters. Each spans 90 degrees of the wheel, which is 16 gates,
# starting at gates 13, 2, 7 and 1. Derived from GATE_WHEEL rather than typed
# out, so it cannot drift from the wheel the rest of the engine uses.
# ---------------------------------------------------------------------------
QUARTER_STARTS = {13: "Initiation", 2: "Civilization",
                  7: "Duality", 1: "Mutation"}

GATE_QUARTER: dict[int, str] = {}
for _start_gate, _name in QUARTER_STARTS.items():
    _i = GATE_WHEEL.index(_start_gate)
    for _j in range(16):
        GATE_QUARTER[GATE_WHEEL[(_i + _j) % 64]] = _name

assert len(GATE_QUARTER) == 64, "quarters must cover all 64 gates exactly once"

CHANNELS: list[tuple[int, int]] = [
    # Head ↔ Ajna
    (64, 47), (61, 24), (63, 4),
    # Ajna ↔ Throat
    (17, 62), (11, 56), (43, 23),
    # Throat ↔ G
    (7, 31), (1, 8), (13, 33), (10, 20),
    # G ↔ Sacral / G ↔ Spleen  [integration circuit through gate 10]
    (10, 34), (10, 57),
    # G ↔ Sacral
    (2, 14), (5, 15), (29, 46),
    # G ↔ Heart
    (25, 51),
    # Sacral ↔ Root
    (3, 60), (9, 52), (42, 53),
    # Sacral ↔ Spleen
    (27, 50), (34, 57),
    # Sacral ↔ SolarPlexus
    (6, 59),
    # Sacral ↔ Throat  [integration circuit shortcut]
    (20, 34),
    # SolarPlexus ↔ Root
    (30, 41), (49, 19), (55, 39),
    # SolarPlexus ↔ Throat
    (12, 22), (35, 36),
    # SolarPlexus ↔ Heart
    (37, 40),
    # Spleen ↔ Root
    (18, 58), (28, 38), (32, 54),
    # Spleen ↔ Throat  [integration circuit]
    (16, 48), (20, 57),
    # Spleen ↔ Heart
    (26, 44),
    # Throat ↔ Heart
    (21, 45),
]
# 36 channels. The integration circuit is the six pairings among gates
# 10/20/34/57: 10-20, 10-34, 10-57, 20-34, 20-57, 34-57.

# Precompute channel lookup: (gate_a, gate_b) → True (canonical form min,max)
_CHANNEL_SET: set[tuple[int, int]] = {(min(a, b), max(a, b)) for a, b in CHANNELS}


def is_channel_defined(gate_a: int, gate_b: int) -> bool:
    return (min(gate_a, gate_b), max(gate_a, gate_b)) in _CHANNEL_SET


# Precompute gate → partner gates (all channels it participates in)
GATE_CHANNEL_PARTNERS: dict[int, list[int]] = {g: [] for g in range(1, 65)}
for _a, _b in CHANNELS:
    GATE_CHANNEL_PARTNERS[_a].append(_b)
    GATE_CHANNEL_PARTNERS[_b].append(_a)


# ---------------------------------------------------------------------------
# Center connectivity (for connected-components / Definition analysis)
# ---------------------------------------------------------------------------
# Two centers are adjacent if at least one channel connects them.
CENTER_ADJACENCY: dict[str, set[str]] = {c: set() for c in CENTERS}
for _a, _b in CHANNELS:
    _ca, _cb = GATE_CENTER[_a], GATE_CENTER[_b]
    if _ca != _cb:
        CENTER_ADJACENCY[_ca].add(_cb)
        CENTER_ADJACENCY[_cb].add(_ca)


# ---------------------------------------------------------------------------
# Motor centers  (motors can be defined and drive Type / MG)
# ---------------------------------------------------------------------------
MOTOR_CENTERS = {"Sacral", "SolarPlexus", "Heart", "Root"}


# ---------------------------------------------------------------------------
# Type determination rules
# (applied after center definition is known)
# ---------------------------------------------------------------------------
def determine_type(defined_centers: set[str],
                   channel_active: set[tuple[int, int]]) -> str:
    """
    Returns one of: Generator, ManifestingGenerator, Manifestor, Projector, Reflector.
    channel_active: set of (min_gate, max_gate) tuples for defined channels.
    """
    has_sacral = "Sacral" in defined_centers

    # Check if any motor connects to Throat directly (via a defined channel)
    motor_to_throat = _motor_connected_to_throat(defined_centers, channel_active)

    if not defined_centers:
        return "Reflector"

    if has_sacral:
        if motor_to_throat:
            return "ManifestingGenerator"
        return "Generator"

    if motor_to_throat:
        return "Manifestor"

    return "Projector"


def _motor_connected_to_throat(defined_centers: set[str],
                                channel_active: set[tuple[int, int]]) -> bool:
    """
    True if a defined motor center is connected to Throat via defined channels only.
    Must traverse the defined-channel center graph (not the full adjacency graph).
    """
    if "Throat" not in defined_centers:
        return False
    motors = MOTOR_CENTERS & defined_centers
    if not motors:
        return False

    # Build adjacency restricted to defined channels
    adj: dict[str, set[str]] = {c: set() for c in defined_centers}
    for ch in channel_active:
        ca = GATE_CENTER[ch[0]]
        cb = GATE_CENTER[ch[1]]
        if ca in defined_centers and cb in defined_centers and ca != cb:
            adj[ca].add(cb)
            adj[cb].add(ca)

    # BFS from Throat via defined-channel edges only
    visited = {"Throat"}
    queue = ["Throat"]
    while queue:
        current = queue.pop()
        for neighbor in adj[current]:
            if neighbor not in visited:
                if neighbor in MOTOR_CENTERS:
                    return True
                visited.add(neighbor)
                queue.append(neighbor)
    return False


# ---------------------------------------------------------------------------
# Authority hierarchy
# ---------------------------------------------------------------------------
AUTHORITY_ORDER = [
    ("SolarPlexus", "Emotional (Solar Plexus)"),
    ("Sacral",      "Sacral"),
    ("Spleen",      "Splenic"),
    ("Heart",       "Ego / Heart"),
    ("G",           "Self-Projected"),
]


def determine_authority(defined_centers: set[str], is_reflector: bool) -> str:
    if is_reflector:
        return "Lunar"
    for center, label in AUTHORITY_ORDER:
        if center in defined_centers:
            return label
    return "Mental / None"


# ---------------------------------------------------------------------------
# Definition (connected-components on the DEFINED center graph)
# ---------------------------------------------------------------------------
def determine_definition(defined_centers: set[str],
                          defined_channels: set[tuple[int, int]]) -> tuple[str, list[set[str]]]:
    """
    Returns (definition_label, list_of_components).
    definition_label: Single, Split, Triple Split, Quadruple Split, or No Definition.
    """
    if not defined_centers:
        return "No Definition", []

    # Build adjacency among DEFINED centers via DEFINED channels
    adj: dict[str, set[str]] = {c: set() for c in defined_centers}
    for ch in defined_channels:
        ca = GATE_CENTER[ch[0]]
        cb = GATE_CENTER[ch[1]]
        if ca in defined_centers and cb in defined_centers and ca != cb:
            adj[ca].add(cb)
            adj[cb].add(ca)

    # BFS connected components
    visited: set[str] = set()
    components: list[set[str]] = []
    for start in sorted(defined_centers):
        if start in visited:
            continue
        comp: set[str] = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for nb in adj[node]:
                if nb not in visited:
                    queue.append(nb)
        components.append(comp)

    n = len(components)
    labels = {1: "Single Definition", 2: "Split Definition",
              3: "Triple Split", 4: "Quadruple Split"}
    return labels.get(n, f"{n}-way Split"), components


# Incarnation Cross naming lives in crosses.py (keyed by four gates + angle).


# ---------------------------------------------------------------------------
# Not-Self themes
# ---------------------------------------------------------------------------
NOT_SELF_THEME = {
    "Generator":           "Frustration",
    "ManifestingGenerator": "Frustration / Anger",
    "Manifestor":          "Anger",
    "Projector":           "Bitterness",
    "Reflector":           "Disappointment",
}

TYPE_STRATEGY = {
    "Generator":           "Respond",
    "ManifestingGenerator": "Respond, then inform",
    "Manifestor":          "Inform before acting",
    "Projector":           "Wait for the invitation",
    "Reflector":           "Wait a lunar cycle",
}
