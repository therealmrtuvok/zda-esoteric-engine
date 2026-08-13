"""
Generates the production bodygraph SVG template (assets/bodygraph.svg).
All geometry lives here and is baked into the static SVG; all color lives
in CSS variables in the consuming page. Rendering is pure data-binding via
element ids: center-{name}, gate-{n}, channel-{lo}-{hi}.

Channels are drawn as TWO halves (one per gate) so hanging gates render as
colored stubs from their center — this is what makes transit completion
visible (the transit supplies the missing half).
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.hd_tables import CHANNELS, GATE_CENTER

W, H = 440, 690

# --- 9 centers: (id, shape points/rect, label position) -------------------
CENTER_SHAPES = {
    "head":        {"kind": "polygon", "pts": [(220, 28), (186, 76), (254, 76)]},
    "ajna":        {"kind": "polygon", "pts": [(186, 114), (254, 114), (220, 162)]},
    "throat":      {"kind": "rect", "x": 188, "y": 208, "w": 64, "h": 64},
    "g":           {"kind": "polygon", "pts": [(220, 312), (264, 356), (220, 400), (176, 356)]},
    "heart":       {"kind": "polygon", "pts": [(282, 402), (330, 402), (306, 440)]},
    "sacral":      {"kind": "rect", "x": 188, "y": 488, "w": 64, "h": 64},
    "spleen":      {"kind": "polygon", "pts": [(44, 484), (112, 448), (112, 520)]},
    "solarplexus": {"kind": "polygon", "pts": [(396, 484), (328, 520), (328, 448)]},
    "root":        {"kind": "rect", "x": 188, "y": 600, "w": 64, "h": 64},
}

# internal center key → engine center name
CENTER_KEY = {
    "Head": "head", "Ajna": "ajna", "Throat": "throat", "G": "g",
    "Heart": "heart", "Sacral": "sacral", "Spleen": "spleen",
    "SolarPlexus": "solarplexus", "Root": "root",
}

# --- 64 gate anchors: gate → (x, y) on its center's edge ------------------
GATE_ANCHORS = {
    # Head (bottom edge)
    64: (200, 76), 61: (220, 76), 63: (240, 76),
    # Ajna (top edge / lower sides)
    47: (200, 114), 24: (220, 114), 4: (240, 114),
    17: (202, 140), 43: (220, 158), 11: (238, 140),
    # Throat
    62: (200, 208), 23: (220, 208), 56: (240, 208),
    16: (188, 222), 20: (188, 250),
    35: (252, 222), 12: (252, 248),
    31: (198, 272), 8: (220, 272), 33: (242, 272), 45: (252, 266),
    # G
    7: (206, 326), 1: (220, 312), 13: (234, 326),
    10: (176, 356), 25: (264, 356),
    15: (206, 386), 2: (220, 400), 46: (234, 386),
    # Heart
    21: (300, 402), 51: (286, 404), 26: (292, 418), 40: (320, 414),
    # Sacral
    5: (200, 488), 14: (220, 488), 29: (240, 488),
    34: (188, 504), 27: (188, 530), 59: (252, 516),
    42: (200, 552), 3: (220, 552), 9: (240, 552),
    # Root
    53: (200, 600), 60: (220, 600), 52: (240, 600),
    54: (188, 614), 38: (188, 632), 58: (188, 650),
    19: (252, 614), 39: (252, 632), 41: (252, 650),
    # Spleen (right edge + lower side)
    48: (112, 456), 57: (112, 472), 44: (112, 488), 50: (112, 504),
    32: (76, 502), 28: (90, 509), 18: (103, 516),
    # Solar Plexus (left edge + lower side)
    22: (328, 456), 36: (328, 472), 37: (328, 488), 6: (328, 504),
    49: (344, 512), 55: (358, 504), 30: (372, 497),
}

# Channels needing a curved route (to avoid crossing another center's body):
# (lo, hi) → SVG path 'd' override for the FULL channel; halves are split at t=0.5
CURVED = {
    (20, 34): "M188,250 C158,320 158,440 188,504",
    (12, 22): "M252,248 C344,300 348,390 328,456",
    (35, 36): "M252,222 C362,282 362,392 328,472",
}


def _midpoint_of_path(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def _bezier_point(p0, c1, c2, p3, t):
    mt = 1 - t
    x = mt**3*p0[0] + 3*mt**2*t*c1[0] + 3*mt*t**2*c2[0] + t**3*p3[0]
    y = mt**3*p0[1] + 3*mt**2*t*c1[1] + 3*mt*t**2*c2[1] + t**3*p3[1]
    return (x, y)


def _parse_curve(d):
    # "M x,y C c1x,c1y c2x,c2y x,y"
    parts = d.replace("M", "").replace("C", " ").split()
    nums = [tuple(map(float, p.split(","))) for p in parts]
    return nums[0], nums[1], nums[2], nums[3]


def emit():
    out = []
    out.append(f'<svg id="bodygraph" viewBox="0 0 {W} {H}" '
               f'xmlns="http://www.w3.org/2000/svg" '
               f'font-family="var(--bg-font, Georgia, serif)">')

    # --- channels first (under centers) ---
    out.append('  <g id="channels">')
    for ga, gb in CHANNELS:
        lo, hi = min(ga, gb), max(ga, gb)
        pa, pb = GATE_ANCHORS[lo], GATE_ANCHORS[hi]
        if (lo, hi) in CURVED:
            p0, c1, c2, p3 = _parse_curve(CURVED[(lo, hi)])
            mid = _bezier_point(p0, c1, c2, p3, 0.5)
            m1 = _bezier_point(p0, c1, c2, p3, 0.25)
            m3 = _bezier_point(p0, c1, c2, p3, 0.75)
            half_a = f"M{p0[0]:.0f},{p0[1]:.0f} Q{m1[0]:.0f},{m1[1]:.0f} {mid[0]:.0f},{mid[1]:.0f}"
            half_b = f"M{mid[0]:.0f},{mid[1]:.0f} Q{m3[0]:.0f},{m3[1]:.0f} {p3[0]:.0f},{p3[1]:.0f}"
        else:
            mid = _midpoint_of_path(pa, pb)
            half_a = f"M{pa[0]},{pa[1]} L{mid[0]:.0f},{mid[1]:.0f}"
            half_b = f"M{mid[0]:.0f},{mid[1]:.0f} L{pb[0]},{pb[1]}"
        out.append(f'    <g id="channel-{lo}-{hi}" class="channel" data-state="open">')
        out.append(f'      <path class="half" data-gate="{lo}" d="{half_a}"/>')
        out.append(f'      <path class="half" data-gate="{hi}" d="{half_b}"/>')
        out.append('    </g>')
    out.append('  </g>')

    # --- centers ---
    out.append('  <g id="centers">')
    for name, s in CENTER_SHAPES.items():
        if s["kind"] == "rect":
            out.append(f'    <rect id="center-{name}" class="center" data-state="open" '
                       f'x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" rx="6"/>')
        else:
            pts = " ".join(f"{x},{y}" for x, y in s["pts"])
            out.append(f'    <polygon id="center-{name}" class="center" data-state="open" '
                       f'points="{pts}"/>')
    out.append('  </g>')

    # --- gate anchors + labels ---
    out.append('  <g id="gates">')
    for gate, (x, y) in sorted(GATE_ANCHORS.items()):
        out.append(f'    <g id="gate-{gate}" class="gate" data-state="open" '
                   f'data-center="{CENTER_KEY[GATE_CENTER[gate]]}">')
        out.append(f'      <circle cx="{x}" cy="{y}" r="7.5"/>')
        out.append(f'      <text x="{x}" y="{y}" text-anchor="middle" '
                   f'dominant-baseline="central" font-size="8.5">{gate}</text>')
        out.append('    </g>')
    out.append('  </g>')

    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    svg = emit()
    dest = os.path.join(os.path.dirname(__file__), "..", "assets", "bodygraph.svg")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        f.write(svg)
    n_channels = svg.count('class="channel"')
    n_gates = svg.count('class="gate"')
    n_centers = svg.count('class="center"')
    print(f"wrote {dest}: {n_centers} centers, {n_gates} gates, {n_channels} channels")
