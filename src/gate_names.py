"""
Gate names.

These are the classical I Ching hexagram names, which predate Human Design by
roughly three thousand years and appear across every translation. They are
deliberately NOT the Jovian Archive keynotes, which are that organisation's
own wording.

Where a hexagram is commonly known by two renderings, both are given so a
reader recognises whichever they were taught.
"""

GATE_NAMES: dict[int, str] = {
    1:  "The Creative",
    2:  "The Receptive",
    3:  "Difficulty at the Beginning",
    4:  "Youthful Folly",
    5:  "Waiting",
    6:  "Conflict",
    7:  "The Army",
    8:  "Holding Together",
    9:  "The Taming Power of the Small",
    10: "Treading",
    11: "Peace",
    12: "Standstill",
    13: "Fellowship",
    14: "Possession in Great Measure",
    15: "Modesty",
    16: "Enthusiasm",
    17: "Following",
    18: "Work on What Has Been Spoiled",
    19: "Approach",
    20: "Contemplation",
    21: "Biting Through",
    22: "Grace",
    23: "Splitting Apart",
    24: "Return",
    25: "Innocence",
    26: "The Taming Power of the Great",
    27: "Nourishment",
    28: "Preponderance of the Great",
    29: "The Abysmal, Water",
    30: "The Clinging, Fire",
    31: "Influence",
    32: "Duration",
    33: "Retreat",
    34: "The Power of the Great",
    35: "Progress",
    36: "Darkening of the Light",
    37: "The Family",
    38: "Opposition",
    39: "Obstruction",
    40: "Deliverance",
    41: "Decrease",
    42: "Increase",
    43: "Breakthrough",
    44: "Coming to Meet",
    45: "Gathering Together",
    46: "Pushing Upward",
    47: "Oppression",
    48: "The Well",
    49: "Revolution",
    50: "The Caldron",
    51: "The Arousing, Thunder",
    52: "Keeping Still, Mountain",
    53: "Gradual Development",
    54: "The Marrying Maiden",
    55: "Abundance",
    56: "The Wanderer",
    57: "The Gentle, Wind",
    58: "The Joyous, Lake",
    59: "Dispersion",
    60: "Limitation",
    61: "Inner Truth",
    62: "Preponderance of the Small",
    63: "After Completion",
    64: "Before Completion",
}


def gate_name(gate: int) -> str:
    return GATE_NAMES.get(gate, f"Gate {gate}")


def channel_name(a: int, b: int) -> str:
    lo, hi = min(a, b), max(a, b)
    return f"{gate_name(lo)} to {gate_name(hi)}"
