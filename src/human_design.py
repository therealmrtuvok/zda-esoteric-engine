"""
Human Design layer — consumes ephemeris_core, never imports swisseph directly.
Computes: Personality + Design activations, gates/lines/channels/centers,
Type, Authority, Profile, Definition, Incarnation Cross, Variable.
"""

from dataclasses import dataclass, field
from .ephemeris_core import calc_chart, calc_at_jd, binary_search_sun_longitude
from .hd_tables import (
    longitude_to_activation,
    opposite_gate,
    GATE_CENTER,
    CHANNELS,
    _CHANNEL_SET,
    CENTERS,
    CENTER_GATES,
    MOTOR_CENTERS,
    determine_type,
    determine_authority,
    determine_definition,
    NOT_SELF_THEME,
    TYPE_STRATEGY,
)
from .crosses import cross_name

# The 13 standard HD activation points (same for Personality and Design).
# Chiron/Juno are astrology-layer bodies only — NOT part of the design chart.
HD_PLANETS = [
    "sun", "earth",    # earth = synthetic (opposite of sun)
    "moon",
    "true_node",       # North Node
    "south_node",      # synthetic (opposite of North Node)
    "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]

PLANET_LABELS = {
    "sun":        "Sun",
    "earth":      "Earth",
    "moon":       "Moon",
    "true_node":  "North Node",
    "south_node": "South Node",
    "mercury":    "Mercury",
    "venus":      "Venus",
    "mars":       "Mars",
    "jupiter":    "Jupiter",
    "saturn":     "Saturn",
    "uranus":     "Uranus",
    "neptune":    "Neptune",
    "pluto":      "Pluto",
    "chiron":     "Chiron",
}


@dataclass
class GateActivation:
    planet: str
    gate: int
    line: int
    color: int
    tone: int
    base: int


@dataclass
class HdChart:
    # Raw activations
    personality: dict[str, GateActivation]   # planet → activation
    design: dict[str, GateActivation]

    # Derived
    all_gates: set[int]          # all activated gate numbers (both sets)
    defined_channels: set[tuple[int, int]]   # (min_gate, max_gate)
    defined_centers: set[str]
    undefined_centers: set[str]

    type_: str
    authority: str
    profile: str                 # e.g. "3/5"
    definition: str              # e.g. "Quadruple Split"
    definition_components: list[set[str]]
    incarnation_cross: str
    variable: str                # e.g. "PLR DLR"
    not_self_theme: str
    strategy: str

    # Timestamps
    birth_julian_day: float
    design_julian_day: float


def _activations_from_positions(positions: dict) -> dict[str, GateActivation]:
    """
    Build gate activations for one set of positions (personality or design).
    positions: dict of planet_name → {longitude, speed, retrograde}
    Adds synthetic Earth (Sun + 180°) and South Node (North Node + 180°).
    """
    out = {}
    sun_lon = positions["sun"]["longitude"]
    node_lon = positions["true_node"]["longitude"]
    positions = dict(positions)
    positions["earth"] = {"longitude": (sun_lon + 180) % 360}
    positions["south_node"] = {"longitude": (node_lon + 180) % 360}

    for planet in HD_PLANETS:
        lon = positions[planet]["longitude"]
        gate, line, color, tone, base = longitude_to_activation(lon)
        out[planet] = GateActivation(
            planet=planet,
            gate=gate,
            line=line,
            color=color,
            tone=tone,
            base=base,
        )
    return out


def _compute_variable(p_activations: dict, d_activations: dict) -> str:
    """
    Variable / PHS four arrows.
    Each arrow is Left (odd color: 1,3,5) or Right (even color: 2,4,6).

    Layout (standard HD design chart):
      Top-right (Determination): Personality Sun color
      Top-left  (Environment):   Design Sun color
      Bottom-right (Motivation): Personality Earth color
      Bottom-left  (Perspective):Design Earth color

    Return format: "PLR DLR"
      P prefix → top-right then top-left (Sun-based)
      D prefix → bottom-right then bottom-left (Earth-based)
    """
    def lr(act: GateActivation) -> str:
        return "L" if act.color % 2 == 1 else "R"

    return (
        f"P{lr(p_activations['sun'])}{lr(d_activations['sun'])}"
        f" D{lr(p_activations['earth'])}{lr(d_activations['earth'])}"
    )


def compute_hd_chart(year: int, month: int, day: int, hour_ut: float,
                     lat: float, lon: float) -> HdChart:
    """
    Main entry point.
    year/month/day: birth date  |  hour_ut: UTC decimal hours
    lat/lon: birth location (degrees, north/east positive)
    """
    # --- Personality (birth) positions ---
    chart = calc_chart(year, month, day, hour_ut, lat, lon)
    birth_jd = chart.julian_day

    # Build position dict for personality
    personality_positions = {
        name: {"longitude": p.longitude, "speed": p.speed, "retrograde": p.retrograde}
        for name, p in chart.planets.items()
    }
    p_acts = _activations_from_positions(personality_positions)

    # --- Design date: find when Sun was exactly (natal_sun_lon - 88°) ---
    natal_sun_lon = chart.planets["sun"].longitude
    design_sun_target = (natal_sun_lon - 88.0) % 360.0

    # Search roughly 85–95 days before birth
    design_jd = binary_search_sun_longitude(
        design_sun_target,
        jd_start=birth_jd - 95,
        jd_end=birth_jd - 80,
    )

    # --- Design positions ---
    design_positions = calc_at_jd(design_jd)
    d_acts = _activations_from_positions(design_positions)

    # --- Gather all activated gates ---
    all_gates: set[int] = set()
    for act in p_acts.values():
        all_gates.add(act.gate)
    for act in d_acts.values():
        all_gates.add(act.gate)

    # --- Find defined channels (both gates active) ---
    defined_channels: set[tuple[int, int]] = set()
    for ga, gb in CHANNELS:
        if ga in all_gates and gb in all_gates:
            defined_channels.add((min(ga, gb), max(ga, gb)))

    # --- Defined centers (touched by at least one defined channel) ---
    center_touched_by_defined: set[str] = set()
    for ga, gb in defined_channels:
        center_touched_by_defined.add(GATE_CENTER[ga])
        center_touched_by_defined.add(GATE_CENTER[gb])

    defined_centers = center_touched_by_defined
    undefined_centers = set(CENTERS) - defined_centers

    # --- Type ---
    type_ = determine_type(defined_centers, defined_channels)

    # --- Authority ---
    is_reflector = (type_ == "Reflector")
    authority = determine_authority(defined_centers, is_reflector)

    # --- Profile: Personality Sun line / Design Sun line ---
    p_sun = p_acts["sun"]
    d_sun = d_acts["sun"]
    profile = f"{p_sun.line}/{d_sun.line}"

    # --- Definition ---
    definition, components = determine_definition(defined_centers, defined_channels)

    # --- Incarnation Cross ---
    cross = cross_name(
        p_sun.gate, p_acts["earth"].gate,
        d_sun.gate, d_acts["earth"].gate,
        p_sun.line, d_sun.line,
    )

    # --- Variable ---
    variable = _compute_variable(p_acts, d_acts)

    return HdChart(
        personality=p_acts,
        design=d_acts,
        all_gates=all_gates,
        defined_channels=defined_channels,
        defined_centers=defined_centers,
        undefined_centers=undefined_centers,
        type_=type_,
        authority=authority,
        profile=profile,
        definition=definition,
        definition_components=components,
        incarnation_cross=cross,
        variable=variable,
        not_self_theme=NOT_SELF_THEME.get(type_, ""),
        strategy=TYPE_STRATEGY.get(type_, ""),
        birth_julian_day=birth_jd,
        design_julian_day=design_jd,
    )


def hd_chart_to_dict(chart: HdChart) -> dict:
    """Serialise an HdChart to a JSON-friendly dict."""

    def act_to_dict(act: GateActivation) -> dict:
        return {
            "gate": act.gate,
            "line": act.line,
            "color": act.color,
            "tone": act.tone,
            "base": act.base,
        }

    return {
        "type": chart.type_,
        "authority": chart.authority,
        "profile": chart.profile,
        "definition": chart.definition,
        "incarnation_cross": chart.incarnation_cross,
        "variable": chart.variable,
        "not_self_theme": chart.not_self_theme,
        "strategy": chart.strategy,
        "defined_centers": sorted(chart.defined_centers),
        "undefined_centers": sorted(chart.undefined_centers),
        "defined_channels": sorted(list(chart.defined_channels)),
        "personality": {p: act_to_dict(a) for p, a in chart.personality.items()},
        "design": {p: act_to_dict(a) for p, a in chart.design.items()},
        "design_julian_day": round(chart.design_julian_day, 5),
        "birth_julian_day": round(chart.birth_julian_day, 5),
    }
