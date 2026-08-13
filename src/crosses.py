"""
Incarnation Cross naming.
The engine computes the four cross gates; this module only NAMES them.
A cross is keyed by (personality_sun, personality_earth, design_sun,
design_earth, angle) — the same four gates produce different named crosses
under different angles, so the angle is part of the key.
"""

# Profile line-pairs → angle
_RAC_PROFILES = {(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6)}
_JUX_PROFILES = {(4, 1)}
_LAC_PROFILES = {(4, 6), (5, 1), (5, 2), (6, 2), (6, 3)}

ANGLE_LABELS = {
    "RAC": "Right Angle",
    "JUX": "Juxtaposition",
    "LAC": "Left Angle",
}


def angle_from_profile(personality_line: int, design_line: int) -> str:
    """Return 'RAC' | 'JUX' | 'LAC' for a profile (e.g. 3,5 → 'RAC')."""
    profile = (personality_line, design_line)
    if profile in _RAC_PROFILES:
        return "RAC"
    if profile in _JUX_PROFILES:
        return "JUX"
    if profile in _LAC_PROFILES:
        return "LAC"
    raise ValueError(f"Unknown profile {personality_line}/{design_line}")


# ---------------------------------------------------------------------------
# Cross name table
# key: (p_sun, p_earth, d_sun, d_earth, angle) → base name (no gate suffix)
# ~192 entries when complete (64 Sun gates × 3 angles).
# Filled from verified references; every entry should be backed by a test
# in tests/test_crosses.py. Unfilled entries fall back gracefully.
# ---------------------------------------------------------------------------
CROSSES: dict[tuple[int, int, int, int, str], str] = {
    # Verified against ahumandesign.com + loveyourhumandesign.com cross lists,
    # spot-checked against humandesign.zone; every entry passes the
    # earth-opposition and 88-degree wheel-offset checks (see tests).
    (1, 2, 7, 13, "RAC"): "Right Angle Cross of the Sphinx",
    (1, 2, 4, 49, "JUX"): "Juxtaposition Cross of Self-Expression",
    (1, 2, 4, 49, "LAC"): "Left Angle Cross of Defiance",
    (2, 1, 13, 7, "RAC"): "Right Angle Cross of the Sphinx",
    (2, 1, 49, 4, "JUX"): "Juxtaposition Cross of the Driver",
    (2, 1, 49, 4, "LAC"): "Left Angle Cross of Defiance",
    (3, 50, 60, 56, "RAC"): "Right Angle Cross of Laws",
    (3, 50, 41, 31, "JUX"): "Juxtaposition Cross of Mutation",
    (3, 50, 41, 31, "LAC"): "Left Angle Cross of Wishes",
    (4, 49, 23, 43, "RAC"): "Right Angle Cross of Explanation",
    (4, 49, 8, 14, "JUX"): "Juxtaposition Cross of Formulization",
    (4, 49, 8, 14, "LAC"): "Left Angle Cross of Revolution",
    (5, 35, 64, 63, "RAC"): "Right Angle Cross of Consciousness",
    (5, 35, 47, 22, "JUX"): "Juxtaposition Cross of Habits",
    (5, 35, 47, 22, "LAC"): "Left Angle Cross of Separation",
    (6, 36, 12, 11, "RAC"): "Right Angle Cross of Eden",
    (6, 36, 15, 10, "JUX"): "Juxtaposition Cross of Conflict",
    (6, 36, 15, 10, "LAC"): "Left Angle Cross of the Plane",
    (7, 13, 2, 1, "RAC"): "Right Angle Cross of the Sphinx",
    (7, 13, 23, 43, "JUX"): "Juxtaposition Cross of Interaction",
    (7, 13, 23, 43, "LAC"): "Left Angle Cross of Masks",
    (8, 14, 30, 29, "RAC"): "Right Angle Cross of Contagion",
    (8, 14, 55, 59, "JUX"): "Juxtaposition Cross of Contribution",
    (8, 14, 55, 59, "LAC"): "Left Angle Cross of Uncertainty",
    (9, 16, 40, 37, "RAC"): "Right Angle Cross of Planning",
    (9, 16, 64, 63, "JUX"): "Juxtaposition Cross of Focus",
    (9, 16, 64, 63, "LAC"): "Left Angle Cross of Identification",
    (10, 15, 46, 25, "RAC"): "Right Angle Cross of Vessel of Love",
    (10, 15, 18, 17, "JUX"): "Juxtaposition Cross of Behavior",
    (10, 15, 18, 17, "LAC"): "Left Angle Cross of Prevention",
    (11, 12, 6, 36, "RAC"): "Right Angle Cross of Eden",
    (11, 12, 46, 25, "JUX"): "Juxtaposition Cross of Ideas",
    (11, 12, 46, 25, "LAC"): "Left Angle Cross of Education",
    (12, 11, 36, 6, "RAC"): "Right Angle Cross of Eden",
    (12, 11, 25, 46, "JUX"): "Juxtaposition Cross of Articulation",
    (12, 11, 25, 46, "LAC"): "Left Angle Cross of Education",
    (13, 7, 1, 2, "RAC"): "Right Angle Cross of the Sphinx",
    (13, 7, 43, 23, "JUX"): "Juxtaposition Cross of Listening",
    (13, 7, 43, 23, "LAC"): "Left Angle Cross of Masks",
    (14, 8, 29, 30, "RAC"): "Right Angle Cross of Contagion",
    (14, 8, 59, 55, "JUX"): "Juxtaposition Cross of Empowering",
    (14, 8, 59, 55, "LAC"): "Left Angle Cross of Uncertainty",
    (15, 10, 25, 46, "RAC"): "Right Angle Cross of the Vessel of Love",
    (15, 10, 17, 18, "JUX"): "Juxtaposition Cross of Extremes",
    (15, 10, 17, 18, "LAC"): "Left Angle Cross of Prevention",
    (16, 9, 37, 40, "RAC"): "Right Angle Cross of Planning",
    (16, 9, 63, 64, "JUX"): "Juxtaposition Cross of Experimentation",
    (16, 9, 63, 64, "LAC"): "Left Angle Cross of Identification",
    (17, 18, 58, 52, "RAC"): "Right Angle Cross of Service",
    (17, 18, 38, 39, "JUX"): "Juxtaposition Cross of Opinions",
    (17, 18, 38, 39, "LAC"): "Left Angle Cross of Upheaval",
    (18, 17, 52, 58, "RAC"): "Right Angle Cross of Service",
    (18, 17, 39, 38, "JUX"): "Juxtaposition Cross of Correction",
    (18, 17, 39, 38, "LAC"): "Left Angle Cross of Upheaval",
    (19, 33, 44, 24, "RAC"): "Right Angle Cross of the Four Ways",
    (19, 33, 1, 2, "JUX"): "Juxtaposition Cross of Need",
    (19, 33, 1, 2, "LAC"): "Left Angle Cross of Refinement",
    (20, 34, 55, 59, "RAC"): "Right Angle Cross of the Sleeping Phoenix",
    (20, 34, 37, 40, "JUX"): "Juxtaposition Cross of the Now",
    (20, 34, 37, 40, "LAC"): "Left Angle Cross of Duality",
    (21, 48, 38, 39, "RAC"): "Right Angle Cross of Tension",
    (21, 48, 54, 53, "JUX"): "Juxtaposition Cross of Control",
    (21, 48, 54, 53, "LAC"): "Left Angle Cross of Endeavour",
    (22, 47, 26, 45, "RAC"): "Right Angle Cross of Rulership",
    (22, 47, 11, 12, "JUX"): "Juxtaposition Cross of Grace",
    (22, 47, 11, 12, "LAC"): "Left Angle Cross of Informing",
    (23, 43, 49, 4, "RAC"): "Right Angle Cross of Explanation",
    (23, 43, 30, 29, "JUX"): "Juxtaposition Cross of Assimilation",
    (23, 43, 30, 29, "LAC"): "Left Angle Cross of Dedication",
    (24, 44, 19, 33, "RAC"): "Right Angle Cross of the Four Ways",
    (24, 44, 13, 7, "JUX"): "Juxtaposition Cross of Rationalization",
    (24, 44, 13, 7, "LAC"): "Left Angle Cross of Incarnation",
    (25, 46, 10, 15, "RAC"): "Right Angle Cross of the Vessel of Love",
    (25, 46, 58, 52, "JUX"): "Juxtaposition Cross of Innocence",
    (25, 46, 58, 52, "LAC"): "Left Angle Cross of Healing",
    (26, 45, 47, 22, "RAC"): "Right Angle Cross of Rulership",
    (26, 45, 6, 36, "JUX"): "Juxtaposition Cross of the Trickster",
    (26, 45, 6, 36, "LAC"): "Left Angle Cross of Confrontation",
    (27, 28, 41, 31, "RAC"): "Right Angle Cross of the Unexpected",
    (27, 28, 19, 33, "JUX"): "Juxtaposition Cross of Caring",
    (27, 28, 19, 33, "LAC"): "Left Angle Cross of Alignment",
    (28, 27, 31, 41, "RAC"): "Right Angle Cross of the Unexpected",
    (28, 27, 33, 19, "JUX"): "Juxtaposition Cross of Risks",
    (28, 27, 33, 19, "LAC"): "Left Angle Cross of Alignment",
    (29, 30, 8, 14, "RAC"): "Right Angle Cross of Contagion",
    (29, 30, 20, 34, "JUX"): "Juxtaposition Cross of Commitment",
    (29, 30, 20, 34, "LAC"): "Left Angle Cross of Industry",
    (30, 29, 14, 8, "RAC"): "Right Angle Cross of Contagion",
    (30, 29, 34, 20, "JUX"): "Juxtaposition Cross of Fates",
    (30, 29, 34, 20, "LAC"): "Left Angle Cross of Industry",
    (31, 41, 27, 28, "RAC"): "Right Angle Cross of the Unexpected",
    (31, 41, 24, 44, "JUX"): "Juxtaposition Cross of Influence",
    (31, 41, 24, 44, "LAC"): "Left Angle Cross of the Alpha",
    (32, 42, 62, 61, "RAC"): "Right Angle Cross of Maya",  # confirmed against Shannon's verified chart
    (32, 42, 56, 60, "JUX"): "Juxtaposition Cross of Conservation",
    (32, 42, 56, 60, "LAC"): "Left Angle Cross of Limitation",
    (33, 19, 24, 44, "RAC"): "Right Angle Cross of the Four Ways",
    (33, 19, 2, 1, "JUX"): "Juxtaposition Cross of Retreat",
    (33, 19, 2, 1, "LAC"): "Left Angle Cross of Refinement",
    (34, 20, 59, 55, "RAC"): "Right Angle Cross of the Sleeping Phoenix",
    (34, 20, 40, 37, "JUX"): "Juxtaposition Cross of Power",
    (34, 20, 40, 37, "LAC"): "Left Angle Cross of Duality",
    (35, 5, 63, 64, "RAC"): "Right Angle Cross of Consciousness",
    (35, 5, 22, 47, "JUX"): "Juxtaposition Cross of Experience",
    (35, 5, 22, 47, "LAC"): "Left Angle Cross of Separation",
    (36, 6, 11, 12, "RAC"): "Right Angle Cross of the Eden",
    (36, 6, 10, 15, "JUX"): "Juxtaposition Cross of Crisis",
    (36, 6, 10, 15, "LAC"): "Left Angle Cross of the Plane",
    (37, 40, 9, 16, "RAC"): "Right Angle Cross of Planning",
    (37, 40, 5, 35, "JUX"): "Juxtaposition Cross of Bargains",
    (37, 40, 5, 35, "LAC"): "Left Angle Cross of Migration",
    (38, 39, 48, 21, "RAC"): "Right Angle Cross of Tension",
    (38, 39, 57, 51, "JUX"): "Juxtaposition Cross of Opposition",
    (38, 39, 57, 51, "LAC"): "Left Angle Cross of Individualism",
    (39, 38, 21, 48, "RAC"): "Right Angle Cross of Tension",
    (39, 38, 51, 57, "JUX"): "Juxtaposition Cross of Provocation",
    (39, 38, 51, 57, "LAC"): "Left Angle Cross of Individualism",
    (40, 37, 16, 9, "RAC"): "Right Angle Cross of Planning",
    (40, 37, 35, 5, "JUX"): "Juxtaposition Cross of Denial",
    (40, 37, 35, 5, "LAC"): "Left Angle Cross of Migration",
    (41, 31, 28, 27, "RAC"): "Right Angle Cross of the Unexpected",
    (41, 31, 44, 24, "JUX"): "Juxtaposition Cross of Fantasy",
    (41, 31, 44, 24, "LAC"): "Left Angle Cross of the Alpha",
    (42, 32, 61, 62, "RAC"): "Right Angle Cross of Maya",
    (42, 32, 60, 56, "JUX"): "Juxtaposition Cross of Completion",
    (42, 32, 60, 56, "LAC"): "Left Angle Cross of Limitation",
    (43, 23, 4, 49, "RAC"): "Right Angle Cross of Explanation",
    (43, 23, 29, 30, "JUX"): "Juxtaposition Cross of Insight",
    (43, 23, 29, 30, "LAC"): "Left Angle Cross of Dedication",
    (44, 24, 33, 19, "RAC"): "Right Angle Cross of the Four Ways",
    (44, 24, 7, 13, "JUX"): "Juxtaposition Cross of Alertness",
    (44, 24, 7, 13, "LAC"): "Left Angle Cross of Incarnation",
    (45, 26, 22, 47, "RAC"): "Right Angle Cross of Rulership",
    (45, 26, 36, 6, "JUX"): "Juxtaposition Cross of Possession",
    (45, 26, 36, 6, "LAC"): "Left Angle Cross of Confrontation",
    (46, 25, 15, 10, "RAC"): "Right Angle Cross of the Vessel of Love",
    (46, 25, 52, 58, "JUX"): "Juxtaposition Cross of Serendipity",
    (46, 25, 52, 58, "LAC"): "Left Angle Cross of Healing",
    (47, 22, 45, 26, "RAC"): "Right Angle Cross of Rulership",
    (47, 22, 12, 11, "JUX"): "Juxtaposition Cross of Oppression",
    (47, 22, 12, 11, "LAC"): "Left Angle Cross of Informing",
    (48, 21, 39, 38, "RAC"): "Right Angle Cross of Tension",
    (48, 21, 53, 54, "JUX"): "Juxtaposition Cross of Depth",
    (48, 21, 53, 54, "LAC"): "Left Angle Cross of Endeavour",
    (49, 4, 43, 23, "RAC"): "Right Angle Cross of Explanation",
    (49, 4, 14, 8, "JUX"): "Juxtaposition Cross of Principles",
    (49, 4, 14, 8, "LAC"): "Left Angle Cross of Revolution",
    (50, 3, 56, 60, "RAC"): "Right Angle Cross of Laws",
    (50, 3, 31, 41, "JUX"): "Juxtaposition Cross of Values",
    (50, 3, 31, 41, "LAC"): "Left Angle Cross of Wishes",
    (51, 57, 54, 53, "RAC"): "Right Angle Cross of Penetration",
    (51, 57, 61, 62, "JUX"): "Juxtaposition Cross of Shock",
    (51, 57, 61, 62, "LAC"): "Left Angle Cross of the Clarion",
    (52, 58, 17, 18, "RAC"): "Right Angle Cross of Service",
    (52, 58, 21, 48, "JUX"): "Juxtaposition Cross of Stillness",
    (52, 58, 21, 48, "LAC"): "Left Angle Cross of Demands",
    (53, 54, 51, 57, "RAC"): "Right Angle Cross of Penetration",
    (53, 54, 42, 32, "JUX"): "Juxtaposition Cross of Beginnings",
    (53, 54, 42, 32, "LAC"): "Left Angle Cross of Cycles",
    (54, 53, 57, 51, "RAC"): "Right Angle Cross of Penetration",
    (54, 53, 32, 42, "JUX"): "Juxtaposition Cross of Ambition",
    (54, 53, 32, 42, "LAC"): "Left Angle Cross of Cycles",
    (55, 59, 34, 20, "RAC"): "Right Angle Cross of the Sleeping Phoenix",
    (55, 59, 9, 16, "JUX"): "Juxtaposition Cross of Moods",
    (55, 59, 9, 16, "LAC"): "Left Angle Cross of Spirit",
    (56, 60, 3, 50, "RAC"): "Right Angle Cross of Laws",
    (56, 60, 27, 28, "JUX"): "Juxtaposition Cross of Stimulation",
    (56, 60, 27, 28, "LAC"): "Left Angle Cross of Distraction",
    (57, 51, 53, 54, "RAC"): "Right Angle Cross of Penetration",
    (57, 51, 62, 61, "JUX"): "Juxtaposition Cross of Intuition",
    (57, 51, 62, 61, "LAC"): "Left Angle Cross of the Clarion",
    (58, 52, 18, 17, "RAC"): "Right Angle Cross of Service",
    (58, 52, 48, 21, "JUX"): "Juxtaposition Cross of Vitality",
    (58, 52, 48, 21, "LAC"): "Left Angle Cross of Demands",
    (59, 55, 20, 34, "RAC"): "Right Angle Cross of the Sleeping Phoenix",
    (59, 55, 16, 9, "JUX"): "Juxtaposition Cross of Strategy",
    (59, 55, 16, 9, "LAC"): "Left Angle Cross of Spirit",
    (60, 56, 50, 3, "RAC"): "Right Angle Cross of Laws",
    (60, 56, 28, 27, "JUX"): "Juxtaposition Cross of Limitation",
    (60, 56, 28, 27, "LAC"): "Left Angle Cross of Distraction",
    (61, 62, 32, 42, "RAC"): "Right Angle Cross of Maya",
    (61, 62, 50, 3, "JUX"): "Juxtaposition Cross of Thinking",
    (61, 62, 50, 3, "LAC"): "Left Angle Cross of Obscuration",
    (62, 61, 42, 32, "RAC"): "Right Angle Cross of Maya",
    (62, 61, 3, 50, "JUX"): "Juxtaposition Cross of Detail",
    (62, 61, 3, 50, "LAC"): "Left Angle Cross of Obscuration",
    (63, 64, 5, 35, "RAC"): "Right Angle Cross of Consciousness",
    (63, 64, 26, 45, "JUX"): "Juxtaposition Cross of Doubts",
    (63, 64, 26, 45, "LAC"): "Left Angle Cross of Dominion",
    (64, 63, 35, 5, "RAC"): "Right Angle Cross of Consciousness",
    (64, 63, 45, 26, "JUX"): "Juxtaposition Cross of Confusion",
    (64, 63, 45, 26, "LAC"): "Left Angle Cross of Dominion",
}


# The cross NAME is determined by (personality sun gate, angle) alone —
# the design gates in a real chart vary. The 88° solar arc spans 15.64
# gate-widths, so the Design Sun sits 15 OR 16 gates back on the wheel
# depending on where within its gate the Personality Sun sits: profile 4/6
# always lands 16 back, while the canonical book quartets assume 15. Keying
# the lookup on all four gates therefore missed every real 4/6 chart —
# caught by the fuzz harness (addendum 3). CROSSES keeps the canonical
# quartets as documentation; the lookup uses this derived index.
_BY_SUN_ANGLE: dict[tuple[int, str], str] = {}
for (_ps, _pe, _ds, _de, _ang), _name in CROSSES.items():
    _key = (_ps, _ang)
    if _key in _BY_SUN_ANGLE and _BY_SUN_ANGLE[_key] != _name:
        raise ValueError(f"conflicting cross names for sun gate/angle {_key}")
    _BY_SUN_ANGLE[_key] = _name


def cross_name(p_sun: int, p_earth: int, d_sun: int, d_earth: int,
               personality_line: int, design_line: int) -> str:
    """
    Full display name for an incarnation cross, e.g.
    "Right Angle Cross of Maya (32/42 | 62/61)". The gate quartet shown is
    the chart's actual gates; the base name resolves by sun gate + angle.
    """
    angle = angle_from_profile(personality_line, design_line)
    base = _BY_SUN_ANGLE.get((p_sun, angle))
    gates = f"({p_sun}/{p_earth} | {d_sun}/{d_earth})"
    if base:
        return f"{base} {gates}"
    return f"Cross of Gates {p_sun}/{p_earth} | {d_sun}/{d_earth} ({angle}, name pending)"
