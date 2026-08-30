"""
Interpretation layer. Turns computed facts into meaning.

Deliberately separate from every calculation module. Nothing here affects a
chart; it only reads finished output and attaches text. That separation matters
for two reasons: the calculations stay verifiable against external sources, and
the copy can be rewritten freely without any risk to correctness.

DRAFT COPY. Written to be accurate to the systems and close to ZDA's register:
direct, unsentimental, no cosmic-instruction voice. It is meant to be edited into
the practitioner's own voice rather than shipped verbatim. Every string is a plain
dict entry, so rewriting the copy needs no code changes.

Voice rules followed here:
  - address the reader as "you"
  - describe mechanics, not destiny; no prediction, no flattery
  - name the difficulty as plainly as the gift
  - short sentences; no exclamation marks; no emoji
"""


# ---------------------------------------------------------------------------
# Display names. The engine's internal centre keys are not reader-facing.
# ---------------------------------------------------------------------------
CENTER_LABELS = {
    "Head": "Head", "Ajna": "Ajna", "Throat": "Throat", "G": "G Centre",
    "Heart": "Heart", "Sacral": "Sacral", "SolarPlexus": "Solar Plexus",
    "Spleen": "Spleen", "Root": "Root",
}

# ---------------------------------------------------------------------------
# Human Design: Type
# ---------------------------------------------------------------------------
TYPES = {
    "Generator": {
        "share": "roughly 37% of people",
        "summary": "You are built to respond, not to initiate.",
        "body": (
            "You have a defined Sacral centre, a consistent renewable engine that "
            "either lights up for something or does not. That engine is not designed "
            "to be pointed at things by your mind. It is designed to answer what "
            "arrives in front of you. When you respond to something that genuinely "
            "moves you, the energy is close to inexhaustible. When you push into "
            "something you decided you should want, the same engine grinds."
        ),
        "strategy": (
            "Wait for something to respond to, then notice what your body does before "
            "your mind explains it. The response comes first."
        ),
        "not_self": (
            "Frustration is the signal that you initiated instead of responded, or "
            "said yes to something your body never actually wanted."
        ),
        "signature": "Satisfaction. The specific tiredness of a day spent well.",
    },
    "ManifestingGenerator": {
        "share": "roughly 33% of people",
        "summary": "You respond like a Generator, then move faster than anyone expects.",
        "body": (
            "You have a defined Sacral and a motor connected to the Throat, so once "
            "you respond to something you can act on it immediately. You skip steps, "
            "find shortcuts, and often have to go back for something you missed. That "
            "is not a flaw in the design; it is the design. You are also rarely doing "
            "one thing, and being told to focus on a single path makes you "
            "smaller rather than more effective."
        ),
        "strategy": (
            "Respond first, then inform the people your speed is about to affect. "
            "The informing is what keeps the resistance down."
        ),
        "not_self": (
            "Frustration and anger together. Frustration from responding wrongly, "
            "anger from moving without telling anyone."
        ),
        "signature": "Satisfaction and peace, in that order.",
    },
    "Projector": {
        "share": "roughly 20% of people",
        "summary": "You are built to guide, and to be invited before you do.",
        "body": (
            "You have no defined Sacral, which means you do not have consistent "
            "energy of your own to burn, and you were never meant to. What you have "
            "instead is the capacity to see other people clearly: how their energy "
            "works, where it is being wasted, what they cannot see about themselves. "
            "That perception is genuinely valuable, and it is also why being ignored "
            "hurts you more than it hurts other types."
        ),
        "strategy": (
            "Wait for recognition and invitation for the things that matter: work, "
            "partnership, where you give your energy. Uninvited insight, however "
            "correct, lands as criticism."
        ),
        "not_self": (
            "Bitterness. The residue of being unseen, or of pushing your way into "
            "rooms you were not invited into."
        ),
        "signature": "Success. Being recognised for what you actually see.",
    },
    "Manifestor": {
        "share": "roughly 9% of people",
        "summary": "You are built to initiate, and to tell people before you do.",
        "body": (
            "You have a motor connected to the Throat without a defined Sacral. That "
            "means you can start things from nothing, without waiting for anyone, "
            "and that your energy comes in bursts rather than as a steady supply. "
            "You are not built to be managed, and most of the friction in a "
            "Manifestor's life comes from other people reacting to being surprised."
        ),
        "strategy": (
            "Inform the people your action will affect before you act. Not permission "
            "Information. It is the single change that removes most resistance."
        ),
        "not_self": (
            "Anger, usually at being controlled, or at the resistance that follows "
            "not informing."
        ),
        "signature": "Peace. The quiet that comes when nobody is pushing back.",
    },
    "Reflector": {
        "share": "about 1% of people",
        "summary": "You have no defined centres. You sample everything around you.",
        "body": (
            "With all nine centres open, you take in and amplify the people and "
            "places around you. You are not a fixed self in the way other types are; "
            "you are a mirror with extraordinary discernment about the health of a "
            "room, a community, a relationship. Who you are around is not a "
            "preference for you. It is the single largest factor in your life."
        ),
        "strategy": (
            "Wait a full lunar cycle, about 28 days, before a significant decision. "
            "You need to feel a thing from every angle the Moon moves you through."
        ),
        "not_self": (
            "Disappointment, usually from being in the wrong environment, or from "
            "deciding too quickly."
        ),
        "signature": "Surprise. Genuine delight at what people can be.",
    },
}

# ---------------------------------------------------------------------------
# Human Design: Authority (how the decision is actually made)
# ---------------------------------------------------------------------------
AUTHORITIES = {
    "Emotional (Solar Plexus)": {
        "summary": "There is no truth in the now. You need time.",
        "body": (
            "You have a defined Solar Plexus, which moves in waves. What feels "
            "certain at the top of a wave reads differently at the bottom, and "
            "neither point is the answer. The clarity is in having ridden the whole "
            "thing. This is why pressure to decide on the spot works so badly on you, "
            "and why sleeping on something is not avoidance but the actual mechanism."
        ),
        "practice": (
            "For anything that matters, say you will come back to it. Then notice how "
            "the same question feels across a few days."
        ),
    },
    "Sacral": {
        "summary": "Your body answers before your mind does.",
        "body": (
            "The Sacral responds in the moment, in sound and impulse rather than "
            "reasoning. A lift toward something, or a flat nothing. It is quick, and "
            "it is reliable, and it is almost always overridden by the story you tell "
            "yourself about what the sensible choice would be."
        ),
        "practice": (
            "Get asked yes-or-no questions out loud. Notice the sound that comes out "
            "before you compose an answer."
        ),
    },
    "Splenic": {
        "summary": "A quiet, instant knowing that does not repeat itself.",
        "body": (
            "The Spleen is the oldest awareness in the body. It registers safety in "
            "the present moment, once, softly. It does not argue, and it will not say "
            "it twice. Most people with Splenic authority can name several times they "
            "knew immediately and talked themselves out of it."
        ),
        "practice": (
            "Notice the first quiet impression, especially the ones that seem to have "
            "no reason attached. That is the signal, not the reasoning that follows."
        ),
    },
    "Ego / Heart": {
        "summary": "The question is whether you actually want to.",
        "body": (
            "Your authority runs through willpower and desire. The honest question is "
            "not whether something is good or worthy. It is whether you want it, and "
            "whether you have the will for it right now. Promises made without that "
            "are the ones that cost you."
        ),
        "practice": "Ask plainly: do I want this? Only commit to what survives that.",
    },
    "Self-Projected": {
        "summary": "You hear your own truth by speaking it out loud.",
        "body": (
            "Your authority runs from the G centre through the Throat, which means "
            "the answer becomes clear in the act of saying it, not in thinking it. "
            "You are not looking for advice when you talk something through. You are "
            "listening to yourself."
        ),
        "practice": (
            "Talk it out with someone who will not interrupt or advise. Listen to what "
            "your own voice does."
        ),
    },
    "Mental / None": {
        "summary": "Your clarity comes from talking, and from where you are.",
        "body": (
            "With no inner motor authority, decisions are not made by an internal "
            "signal. They come from being in the right environment and thinking out "
            "loud with people you trust, not for their opinions, but to hear yourself "
            "in the presence of others."
        ),
        "practice": (
            "Pay close attention to place. The right room makes the decision obvious; "
            "the wrong one makes everything murky."
        ),
    },
    "Lunar": {
        "summary": "Give it a full lunar cycle.",
        "body": (
            "As a Reflector you have no consistent inner authority by design. Clarity "
            "comes from time, roughly 28 days, during which the Moon moves you "
            "through every gate and lets you feel the decision from every angle."
        ),
        "practice": "Track the decision across a month. Talk to trusted people throughout.",
    },
}

# ---------------------------------------------------------------------------
# Human Design: Profile lines
# ---------------------------------------------------------------------------
LINES = {
    1: ("Investigator", "You need to know the foundation before you feel secure. "
        "Research is not procrastination for you; it is how the ground gets solid."),
    2: ("Hermit", "You have natural talent you did not study for, and you need to be "
        "left alone for it to work. Being called out of that is the recurring theme."),
    3: ("Martyr", "You learn by trying things and finding out what does not work. "
        "That is not failure; it is the method. Very little of it is wasted."),
    4: ("Opportunist", "Your life moves through relationships. Opportunity arrives "
        "through people who already know you, which makes your network the asset."),
    5: ("Heretic", "People project onto you. They expect you to have the answer. "
        "You can deliver practical solutions, but the projection is the thing to watch."),
    6: ("Role Model", "You live in three phases: trial and error until about thirty, "
        "then a period on the roof observing, then re-emergence as someone people trust."),
}

# ---------------------------------------------------------------------------
# Human Design: Centres
# ---------------------------------------------------------------------------
CENTERS = {
    "Head":        ("Inspiration and mental pressure",
                    "Questions arrive on their own schedule and they are yours. You "
                    "are not looking for something to wonder about; the wondering "
                    "starts on its own, and it does not switch off because the "
                    "timing is inconvenient.",
                    "You take in other people's questions and can feel pressured to "
                    "answer things that were never yours to solve. The pressure is "
                    "real. The obligation is borrowed."),
    "Ajna":        ("Conceptualisation",
                    "You process the same way every time. That consistency is why "
                    "people bring you things to make sense of, and why changing your "
                    "mind takes actual evidence rather than a good argument.",
                    "You think in many ways rather than one, which is flexible, and "
                    "makes pretending to be certain a real temptation."),
    "Throat":      ("Expression and manifestation",
                    "You have steady access to saying and doing. Not necessarily "
                    "eloquence. Availability. The channel is open whether or not "
                    "the room is listening, which is worth knowing before you "
                    "wonder why you filled a silence.",
                    "You may talk to be noticed, or wait a long time to be asked."),
    "G":           ("Identity, direction and love",
                    "You know who you are without checking. Direction comes from "
                    "inside rather than from the room you are standing in, so when "
                    "you feel lost it is usually a question of what to do next, "
                    "not of who is asking.",
                    "Your direction changes with place and company, which is why "
                    "environment matters more for you than for most."),
    "Heart":       ("Willpower and worth",
                    "Willpower is on tap. You can commit to a thing and deliver it, "
                    "which means the promises you make are worth something and the "
                    "ones you make lightly will still cost you.",
                    "You over-promise to prove your worth. There is nothing to "
                    "prove."),
    "SolarPlexus": ("Emotions",
                    "The waves are yours. They are not a reaction to the room and "
                    "not evidence that something is wrong. They are the weather of "
                    "the system you were built with, and the whole point of the "
                    "wave is that it moves.",
                    "You amplify the emotional weather of the room and can mistake "
                    "it for your own. Distance usually resolves it."),
    "Sacral":      ("Life force and work",
                    "There is a renewable supply here, and it is selective. It "
                    "answers what genuinely interests you and goes flat on what "
                    "does not, which is information rather than a discipline "
                    "problem.",
                    "You do not have your own steady supply. Knowing when enough is "
                    "enough is the whole skill."),
    "Spleen":      ("Intuition, health and fear",
                    "A consistent baseline sense of whether you are alright. It is "
                    "quiet and it is fast, and because it never raises its voice it "
                    "is the easiest thing in your chart to talk yourself out of.",
                    "You amplify fear that is not yours, and can hold onto things "
                    "and people past their time."),
    "Root":        ("Pressure and drive",
                    "Pressure is a constant, not an event. You are built to run "
                    "under load, which is why an empty week can feel worse than a "
                    "full one.",
                    "You feel rushed by pressure that belongs to other people, and "
                    "can hurry to be free of it."),
}


# ---------------------------------------------------------------------------
# Human Design: Definition
# What Definition describes is connection, not quantity. Two people can have
# the same number of defined centres and a completely different chart shape.
# ---------------------------------------------------------------------------
DEFINITIONS = {
    "Single Definition": {
        "share": "roughly 41% of people",
        "summary": "Everything defined in you is connected to everything else defined in you.",
        "body": (
            "One continuous circuit. Whatever is fixed in your design can reach "
            "the rest of what is fixed in your design without going through "
            "anyone. That reads as self-contained, and it is the reason "
            "you can process something on your own and arrive somewhere without "
            "having talked it through."
        ),
        "practical": (
            "You are not dependent on other people to feel complete in yourself. "
            "That is a genuine advantage and it can also make you slower to "
            "notice when you have gone too long without company."
        ),
    },
    "Split Definition": {
        "share": "roughly 45% of people, the most common configuration",
        "summary": "Your definition sits in two separate groups that do not touch.",
        "body": (
            "Two circuits, no bridge between them. The gap is not a deficiency; "
            "it is the shape of the design. In practice, certain things in you "
            "do not automatically talk to each other. Another person standing "
            "nearby connects them, without either of you doing anything "
            "deliberate."
        ),
        "practical": (
            "You are likely to feel more like yourself around some people than "
            "others, and it is worth noticing which. That is not neediness. It "
            "is a mechanical fact about which gates complete your gap."
        ),
    },
    "Triple Split": {
        "share": "roughly 11% of people",
        "summary": "Three separate areas of definition, none of them connected.",
        "body": (
            "Three circuits running in parallel. More of you is fixed than in a "
            "typical chart, and less of it is joined up, so your internal "
            "processing has more places where it does not automatically carry "
            "across. Busier environments often suit you better than quiet ones, "
            "because more people means more of the gaps get bridged."
        ),
        "practical": (
            "Give things more time than feels reasonable. Multiple splits means "
            "information has further to travel before it lands as a decision."
        ),
    },
    "Quadruple Split": {
        "share": "roughly 0.6% of people, the rarest configuration",
        "summary": "Four separate areas of definition, none of them connected.",
        "body": (
            "A great deal of you is fixed, and almost none of it is joined up. "
            "That combination is unusual enough that most descriptions of Human "
            "Design will not describe your experience well. The practical effect "
            "is not fragility. It is that you are consistent in four separate "
            "ways at once, and integrating them is slow work rather than "
            "automatic."
        ),
        "practical": (
            "Patience with your own process is not optional here. Being around "
            "other people does more of the joining than effort does, and rushing "
            "a decision skips the part where the pieces meet."
        ),
    },
    "No Definition": {
        "share": "about 1% of people",
        "summary": "Nothing is fixed. You have no definition at all.",
        "body": (
            "With no defined centres there is no consistent internal circuitry to "
            "run on. What you have instead is total permeability: you take the "
            "shape of what is around you, and you can read a room with a "
            "precision that fixed people cannot."
        ),
        "practical": (
            "Environment and company are not preferences for you. They are the "
            "largest variable in your life, and time is the only reliable filter."
        ),
    },
}

# ---------------------------------------------------------------------------
# Numerology: Life Path
# ---------------------------------------------------------------------------
LIFE_PATHS = {
    1: ("The Initiator", "Independence and starting things. The lesson is doing it "
        "your own way without needing to do it alone."),
    2: ("The Diplomat", "Partnership, sensitivity and timing. The lesson is holding "
        "your own position while staying in relationship."),
    3: ("The Communicator", "Expression, creativity and voice. The lesson is finishing "
        "what you start rather than scattering the energy."),
    4: ("The Builder", "Structure, work and foundations. The lesson is building "
        "something that lasts without turning rigid."),
    5: ("The Seeker", "Freedom, change and experience. The lesson is choosing what to "
        "stay committed to when everything is interesting."),
    6: ("The Nurturer", "Responsibility, care and home. The lesson is carrying what is "
        "actually yours and putting down what is not."),
    7: ("The Mystic", "Study, solitude and depth. The lesson is going inward without "
        "disappearing from your own life."),
    8: ("The Steward", "Power, resources and consequence. The lesson is authority used "
        "well, and a healthy relationship with money."),
    9: ("The Old Soul", "Completion, compassion and release. The lesson is letting go "
        "of what has finished."),
    11: ("The Illuminator", "A master number. Heightened intuition and nervous system. "
         "The lesson is grounding the sensitivity so it is usable."),
    22: ("The Master Builder", "A master number. Large-scale vision made practical. "
         "The lesson is starting small enough to actually begin."),
    33: ("The Teacher", "A master number. Service and care at scale. The lesson is not "
         "losing yourself inside the giving."),
}

# ---------------------------------------------------------------------------
# Numerology: Personal Year (the cycle you are currently inside)
# ---------------------------------------------------------------------------
PERSONAL_YEARS = {
    1: "A beginning. Plant things. What starts now sets the tone for nine years.",
    2: "Slower, relational, patient. Things develop rather than launch.",
    3: "Expression and visibility. Say the thing; make the work public.",
    4: "Work and structure. Unglamorous and foundational. Do the admin.",
    5: "Change and movement. Keep your commitments loose enough to move.",
    6: "Responsibility, home and relationships. Care work comes due.",
    7: "Inward. Study, rest, reassess. A poor year to force outcomes.",
    8: "Consequence and reward. Money, authority and recognition surface.",
    9: "Completion. Endings and clearing out, making room for the next cycle.",
    # reduce() keeps master numbers, so personal_year() genuinely returns 11
    # and 22 for some birth dates. Omitting them here produced a personal year
    # with empty interpretation text and no error, because the lookup uses
    # .get() with a default. Silent, plausible, wrong.
    11: "A 2 year with the volume up. Relational and intuitive, and more "
        "exposed than a 2. Sensitivity is the mechanic, not a side effect.",
    22: "A 4 year at scale. Building something structural that outlasts you. "
        "The work is unglamorous and the horizon is long.",
}


# ---------------------------------------------------------------------------
# Incarnation cross and Variable.
#
# crosses.py names all 192 crosses but carries no descriptive text, and there
# was none for Variable either. Rather than invent 192 write-ups, these
# explain the mechanism and then hand back the four gates, whose themes come
# from the gate table. Honest about what is structural and what is specific.
# ---------------------------------------------------------------------------
CROSS_FRAME = (
    "Your cross is four gates. Two are where the Sun and Earth sat when you "
    "were born. Two are where they sat about three months earlier, which is "
    "the second half of a Human Design chart. It is the biggest and slowest "
    "theme in the whole thing. Unlike Type or Authority, it is not something "
    "you use day to day. You read it backwards, years later, as a description "
    "of what you kept circling."
)

# The angle is decided entirely by the conscious Sun's line. Lines 1 to 3 are
# the lower trigram of the hexagram, the inner half, and give a Right Angle.
# Lines 4 to 6 are the upper trigram, the outer half, and give a Left Angle.
# The single exception is 4/1, which is its own category.
#
# Proportions below are measured, not folklore: 1,200 randomly sampled charts
# gave 50.7% Right Angle, 47.6% Left Angle, 1.8% Juxtaposition.
ANGLES = {
    "Right Angle": (
        "Your conscious Sun sits in the lower trigram of its hexagram, lines "
        "1 to 3, which is the inner half. The theme is worked out through "
        "your own experience rather than delivered to you by other people. "
        "About half of charts are Right Angle, so this is the ordinary case "
        "rather than a distinction. It does not mean self-absorbed. It means "
        "the material is yours to run rather than to receive."
    ),
    "Juxtaposition": (
        "Profile 4/1, and nothing else. Under 2% of charts. Neither turned "
        "inward like a Right Angle nor outward like a Left Angle, but fixed "
        "on one thing, with little of the negotiability the other two have."
    ),
    "Left Angle": (
        "Your conscious Sun sits in the upper trigram, lines 4 to 6, the "
        "outer half. The theme arrives through other people and through "
        "encounters you did not arrange. Just under half of charts."
    ),
}

# Standard Human Design calls these personal and transpersonal karma. That is
# a claim about destiny, which this project does not make. The mechanism is
# trigram position, and the rest is interpretation.

VARIABLE_FRAME = (
    "Variable is the four arrows, written here as two groups: Design on the "
    "left, Personality on the right, each as a pair of Left or Right. It "
    "describes how you take in information and how you focus, not what you "
    "should do. It is the least settled part of the system and the part most "
    "often overstated. Treat it as a hint, not an instruction."
)

VARIABLE_LETTERS = {
    "L": "Left: active, focused, strategic. Takes a specific thing and works it.",
    "R": "Right: passive, receptive, peripheral. Takes the whole field in and "
         "lets it sort itself.",
}


QUARTERS = {
    "Initiation": "Purpose fulfilled through mind. The material is ideas and "
                  "the awakening of them.",
    "Civilization": "Purpose fulfilled through form. Building, structure and "
                    "the made world.",
    "Duality": "Purpose fulfilled through bonding. Relationship is the "
               "vehicle, not the decoration.",
    "Mutation": "Purpose fulfilled through transformation. Change carried in "
                "the body rather than decided in the head.",
}

# Only the Personality Sun's quarter carries a reading. The other three cross
# gates sit roughly 88, 180 and 268 degrees away, and the quarters are 90
# degree blocks, so all four land in different quarters in about 97% of
# charts. A four-quarter spread is the ordinary case, not a distinction.
QUARTER_SPREAD_NOTE = (
    "Your four cross gates fall in four different quarters, which is true of "
    "roughly 97% of charts and follows from the geometry rather than meaning "
    "anything. The quarter that carries a reading is the Personality Sun's."
)


def interpret_cross(hd: dict) -> dict:
    """Cross name, angle explanation, and the four gates that compose it."""
    name = hd.get("incarnation_cross", "")
    angle = next((a for a in ANGLES if name.startswith(a)), None)
    gates = []
    for side in ("personality", "design"):
        for body in ("sun", "earth"):
            act = hd.get(side, {}).get(body)
            if act:
                gates.append({"side": side, "body": body, "gate": act["gate"],
                              "line": act["line"]})
    from .hd_tables import GATE_QUARTER
    for g in gates:
        g["quarter"] = GATE_QUARTER[g["gate"]]
    p_sun = next((g for g in gates
                  if g["side"] == "personality" and g["body"] == "sun"), None)
    quarter = p_sun["quarter"] if p_sun else None
    return {
        "name": name,
        "angle": angle,
        "angle_text": ANGLES.get(angle, ""),
        "frame": CROSS_FRAME,
        "gates": gates,
        "quarter": quarter,
        "quarter_text": QUARTERS.get(quarter, ""),
        "quarter_note": QUARTER_SPREAD_NOTE,
    }


def interpret_variable(hd: dict) -> dict:
    variable = hd.get("variable", "")
    letters = [c for c in variable if c in ("L", "R")]
    return {
        "variable": variable,
        "frame": VARIABLE_FRAME,
        "letters": [VARIABLE_LETTERS[c] for c in dict.fromkeys(letters)],
    }


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def interpret_human_design(hd: dict) -> dict:
    """Attach interpretation text to a computed HD chart dict."""
    type_key = (hd.get("type") or "").replace(" ", "")
    t = TYPES.get(type_key) or TYPES.get(hd.get("type"), {})
    auth = AUTHORITIES.get(hd.get("authority"), {})

    profile = hd.get("profile") or ""
    lines = []
    for part in profile.split("/"):
        if part.strip().isdigit():
            n = int(part)
            if n in LINES:
                lines.append({"line": n, "name": LINES[n][0], "text": LINES[n][1]})

    defined = hd.get("defined_centers") or []
    centres = []
    for name, (title, when_defined, when_open) in CENTERS.items():
        is_def = name in defined
        centres.append({
            "center": name, "label": CENTER_LABELS.get(name, name),
            "theme": title, "defined": is_def,
            "text": when_defined if is_def else when_open,
        })

    defn = DEFINITIONS.get(hd.get("definition"), {})

    return {
        "type": {"name": hd.get("type"), **t},
        "definition": {"name": hd.get("definition"), **defn},
        "authority": {"name": hd.get("authority"), **auth},
        "profile": {"profile": profile, "lines": lines},
        "centers": centres,
    }


def interpret_numerology(num: dict) -> dict:
    lp = num.get("life_path")
    py = num.get("personal_year")
    lp_name, lp_text = LIFE_PATHS.get(lp, ("", ""))
    return {
        "life_path": {"number": lp, "name": lp_name, "text": lp_text},
        "personal_year": {"number": py, "text": PERSONAL_YEARS.get(py, "")},
    }


def interpret_chart(human_design: dict = None, numerology: dict = None) -> dict:
    out = {}
    if human_design:
        out["human_design"] = interpret_human_design(human_design)
    if numerology:
        out["numerology"] = interpret_numerology(numerology)
    return out
