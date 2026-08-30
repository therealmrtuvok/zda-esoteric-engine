"""
Meaning tables for the Human Design layer of the energy calendar.

House style, enforced deliberately:
  - Names here are plain descriptions of what the channel does. They are NOT
    Jovian Archive keynotes. Gate names come from gate_names.py, which uses
    the classical I Ching hexagram names.
  - Mechanics, not destiny. No prediction. No flattery. The difficulty is
    named as plainly as the gift, because a transit that hands you something
    you do not natively have is a loan, not a gift, and the drop when it
    closes is the part people are unprepared for.
  - No em dashes anywhere.

Centres are deliberately NOT duplicated here. They are derived from
hd_tables.GATE_CENTER at import time. Every documented bug in this engine has
been a mapping table repeated in two places and drifting; this file refuses to
be the second copy.

Field contract per channel:
  name          plain descriptive label
  mechanic      what the channel does whenever it is defined, natal or transit
  transit_gift  what becomes available on the days a transit completes it
  good_for      concrete uses, phrased as actions you could actually take
  difficulty    the cost, and what the closing of the window feels like
"""

from .hd_tables import CHANNELS, GATE_CENTER
from .gate_names import GATE_NAMES

CHANNEL_MEANINGS: dict[tuple[int, int], dict] = {

    (1, 8): {
        "name": "Expression and Contribution",
        "mechanic": "Turns a private creative direction into something other "
                    "people can actually see. Gate 1 has the material, gate 8 "
                    "makes the case for it in public.",
        "transit_gift": "The bridge from what you have made to an audience for "
                        "it. Work that has been sitting finished and unshown "
                        "becomes possible to show.",
        "good_for": ["publishing or shipping something already made",
                     "pitching your own work rather than someone else's",
                     "deciding how a finished piece should be presented"],
        "difficulty": "It amplifies whatever is there. It does not improve the "
                      "work. Showing something unfinished on this window is "
                      "still showing something unfinished.",
    },

    (2, 14): {
        "name": "Direction and Fuel",
        "mechanic": "Attaches usable energy to a sense of direction. Gate 2 "
                    "knows which way to face, gate 14 supplies the power to "
                    "actually move that way.",
        "transit_gift": "Direction stops being theoretical. If you hold gate 2 "
                        "and lack 14, you generally know where you are pointed "
                        "and have no engine for it. On these days the engine "
                        "arrives from outside.",
        "good_for": ["starting the thing you have been circling for months",
                     "committing resources, not just intentions",
                     "physical work on a project rather than planning it"],
        "difficulty": "The fuel is borrowed. Do not size the commitment to the "
                      "energy you feel on the day. When it closes, the "
                      "direction remains and the drive does not, which reads "
                      "as failure and is not.",
    },

    (3, 60): {
        "name": "Beginning Under Limits",
        "mechanic": "Turns constraint into a start. Gate 60 holds the limit, "
                    "gate 3 makes the first ordered move inside it.",
        "transit_gift": "Access to starting something without first removing "
                        "the obstacle. The limitation stops being a reason to "
                        "wait.",
        "good_for": ["a first version of something under real constraints",
                     "working with the budget, time or body you actually have",
                     "breaking a stalled project into a single next step"],
        "difficulty": "This is mutative pressure, and it is uncomfortable by "
                      "design. It can present as agitation with nowhere to go "
                      "if you have no concrete thing to begin.",
    },

    (4, 63): {
        "name": "Doubt and the Answer to It",
        "mechanic": "Runs a suspicion through to a possible explanation. Gate "
                    "63 doubts the pattern, gate 4 offers a formula that would "
                    "resolve it.",
        "transit_gift": "The mental loop closes. Questions that have been "
                        "circling get a workable hypothesis attached.",
        "good_for": ["writing down the answer you have been unable to phrase",
                     "auditing something you suspect is wrong",
                     "research, review, and checking your own reasoning"],
        "difficulty": "An answer here is a hypothesis, not a verified fact. "
                      "This is head pressure, and pressure wants relief more "
                      "than it wants accuracy. Test before acting.",
    },

    (5, 15): {
        "name": "Rhythm and Its Range",
        "mechanic": "Sets a consistent pattern and decides how much variation "
                    "it can absorb. Gate 5 keeps the beat, gate 15 stretches it.",
        "transit_gift": "The ability to establish or reset a routine, and to "
                        "let it flex without abandoning it.",
        "good_for": ["rebuilding a sleep, eating or work rhythm",
                     "setting a schedule you intend to keep for months",
                     "returning to a practice you dropped"],
        "difficulty": "A rhythm set on borrowed consistency will need a real "
                      "reason to survive the window. Build the routine around "
                      "something structural, not around how steady you feel.",
    },

    (6, 59): {
        "name": "Intimacy and Its Boundary",
        "mechanic": "Governs how close another person is allowed to get. Gate "
                    "59 works through the barrier, gate 6 decides when it opens "
                    "and when it does not.",
        "transit_gift": "Selective permeability. The capacity to be genuinely "
                        "open to one person without being open to everyone.",
        "good_for": ["a conversation that needs real honesty",
                     "repairing a relationship that stalled on distance",
                     "deciding a boundary rather than defending one"],
        "difficulty": "This runs through the emotional centre, so nothing here "
                      "is trustworthy in the moment. Emotional clarity comes "
                      "over time, never on the day. Do not conclude anything "
                      "about a relationship inside a single window.",
    },

    (7, 31): {
        "name": "Leading by Being Followed",
        "mechanic": "Puts a direction into words that other people will move "
                    "behind. Gate 7 sees the route, gate 31 speaks it as "
                    "influence rather than as an order.",
        "transit_gift": "Your read on where something should go becomes "
                        "communicable and other people can act on it.",
        "good_for": ["presenting a plan to a group",
                     "taking a lead role in something already underway",
                     "writing the strategy document, not just holding it"],
        "difficulty": "Influence here is conditional on being asked. Pushing "
                      "it on people who have not invited it converts the same "
                      "energy into resistance.",
    },

    (9, 52): {
        "name": "Stillness and Focus",
        "mechanic": "Concentrates energy onto detail. Gate 52 holds still, "
                    "gate 9 spends that stillness on one small thing at a time.",
        "transit_gift": "Sustained attention on detail work that normally "
                        "scatters.",
        "good_for": ["the tedious, precise part of a project",
                     "proofing, reconciling, debugging, tidying data",
                     "one long uninterrupted work block"],
        "difficulty": "Focus this narrow loses the shape of the whole. Check "
                      "at the end of the window that the detail you perfected "
                      "was the detail that mattered.",
    },

    (10, 20): {
        "name": "Self in the Present",
        "mechanic": "Puts behaviour and self-knowledge into the current "
                    "moment. Gate 10 is how you conduct yourself, gate 20 "
                    "makes it present tense.",
        "transit_gift": "You can act like yourself in real time rather than "
                        "recognising afterwards what you should have said.",
        "good_for": ["a conversation where you need to be straight",
                     "showing up as yourself somewhere that usually flattens you",
                     "noticing your own behaviour while it is happening"],
        "difficulty": "It surfaces behaviour, including the behaviour you were "
                      "avoiding looking at. Self-awareness is not always a "
                      "pleasant delivery.",
    },

    (10, 34): {
        "name": "Self-Powered Action",
        "mechanic": "Applies raw power to being yourself. Gate 34 is available "
                    "force, gate 10 aims it at your own conduct rather than at "
                    "a task.",
        "transit_gift": "Energy to do the thing that is yours to do, without "
                        "needing anyone to authorise it.",
        "good_for": ["acting on your own behalf, not someone else's",
                     "physical effort undertaken for its own sake",
                     "a decision you have been waiting for permission on"],
        "difficulty": "Power turned on the self with no external check reads "
                      "as stubbornness from outside. It is genuinely hard to "
                      "tell conviction from momentum inside this window.",
    },

    (10, 57): {
        "name": "Self and Instinct",
        "mechanic": "Couples behaviour to an in-the-moment sense of safety. "
                    "Gate 57 hears what is off, gate 10 adjusts conduct to it.",
        "transit_gift": "Reliable instinct about whether a situation is right "
                        "for you, delivered as a body sense rather than a "
                        "reason.",
        "good_for": ["deciding whether to enter a room, deal or arrangement",
                     "trusting a first impression you would normally argue with",
                     "leaving something early"],
        "difficulty": "Spleen speaks once, quietly, and does not repeat. If "
                      "you talk yourself out of it you will not get a second "
                      "signal in the same window.",
    },

    (11, 56): {
        "name": "Ideas and the Telling of Them",
        "mechanic": "Turns ideas into stories that hold attention. Gate 11 "
                    "collects the idea, gate 56 finds the version worth "
                    "listening to.",
        "transit_gift": "Ideas that have been unshareable become tellable.",
        "good_for": ["writing, teaching, drafting the talk",
                     "explaining something you understand but cannot usually convey",
                     "capturing ideas before they evaporate"],
        "difficulty": "Ideas here are stimulation, not instruction. A good "
                      "story about a plan is not evidence the plan is sound, "
                      "and this channel is very good at making it sound sound.",
    },

    (12, 22): {
        "name": "Mood and What It Permits",
        "mechanic": "Gates expression through emotional state. Gate 22 opens "
                    "or closes to people, gate 12 finds articulation only when "
                    "the mood allows.",
        "transit_gift": "Language for something you feel and normally cannot "
                        "say. Access to the social grace that makes it "
                        "receivable.",
        "good_for": ["the difficult message, written not sent",
                     "creative work with emotional content",
                     "social contact you have been avoiding"],
        "difficulty": "Emotional, so not trustworthy inside the day. This "
                      "channel is capable of saying something perfectly and "
                      "wrongly. Draft on the window, send after it.",
    },

    (13, 33): {
        "name": "Witness and Retelling",
        "mechanic": "Gathers what happened and tells it back with the lesson "
                    "intact. Gate 13 receives and holds, gate 33 withdraws and "
                    "then recounts.",
        "transit_gift": "Perspective on your own recent past. The ability to "
                        "say what an experience actually was.",
        "good_for": ["reviewing the last month or year",
                     "journalling with intent, not just logging",
                     "being the person others tell things to"],
        "difficulty": "It needs retreat before it can retell. Trying to "
                      "process in company on this window usually produces "
                      "neither the privacy nor the account.",
    },

    (16, 48): {
        "name": "Depth and the Willingness to Try",
        "mechanic": "Connects a deep well of skill to the enthusiasm that "
                    "risks using it. Gate 48 holds the depth, gate 16 commits "
                    "to the attempt.",
        "transit_gift": "The gap between knowing how and doing it closes. "
                        "Skill you have been rehearsing becomes performable.",
        "good_for": ["the first real attempt at something practised",
                     "auditioning, demoing, going live",
                     "committing to a skill rather than researching it further"],
        "difficulty": "Gate 48's shadow is a fear of inadequacy and it does "
                      "not disappear on the window, it just gets outvoted. "
                      "Enthusiasm without preparation is still unprepared.",
    },

    (17, 62): {
        "name": "Opinion With Evidence",
        "mechanic": "Attaches detail to a point of view so it can be argued. "
                    "Gate 17 forms the opinion, gate 62 supplies the facts and "
                    "names.",
        "transit_gift": "You can back a position instead of just holding it.",
        "good_for": ["making the case with numbers attached",
                     "organising an argument before a meeting",
                     "documenting why a decision was made"],
        "difficulty": "An opinion with supporting detail is still an opinion. "
                      "This channel makes being wrong sound rigorous.",
    },

    (18, 58): {
        "name": "Correction and the Joy of It",
        "mechanic": "Finds the flaw in a pattern and enjoys fixing it. Gate 58 "
                    "supplies the appetite, gate 18 supplies the eye for what "
                    "is wrong.",
        "transit_gift": "Improvement work stops feeling like criticism and "
                        "starts feeling like satisfaction.",
        "good_for": ["fixing the process everyone complains about",
                     "editing, refactoring, quality passes",
                     "reviewing something you are close to"],
        "difficulty": "The eye for what is wrong does not switch off at the "
                      "boundary of things that asked to be improved. Aim it at "
                      "systems on these days, not at people.",
    },

    (19, 49): {
        "name": "Need and the Terms of Meeting It",
        "mechanic": "Senses what is needed and decides whether the arrangement "
                    "is acceptable. Gate 19 feels the want, gate 49 sets the "
                    "conditions and will break the deal over them.",
        "transit_gift": "Clarity about what you need from an arrangement and "
                        "what you will not accept in exchange.",
        "good_for": ["renegotiating terms in work or a relationship",
                     "asking for the thing you have been going without",
                     "noticing which arrangements are actually working"],
        "difficulty": "Emotional and abrupt. Gate 49 revolts rather than "
                      "renegotiates when pushed. Name the terms on the window "
                      "and decide across several of them.",
    },
    (20, 34): {
        "name": "Power in the Present",
        "mechanic": "Converts available force directly into action now, with "
                    "no deliberation in between. Gate 34 is the power, gate 20 "
                    "is the immediacy.",
        "transit_gift": "The capacity to just do it, in the moment, without "
                        "the run-up. Busy in a way that actually produces "
                        "something.",
        "good_for": ["the task that only ever gets done in one sitting",
                     "physical work, clearing, moving, making",
                     "acting on something already decided"],
        "difficulty": "This is the busiest energy in the system and it does "
                      "not ask where it is going. Decide the target before the "
                      "window opens, or it will spend itself on whatever is "
                      "nearest.",
    },

    (20, 57): {
        "name": "Instinct Spoken Now",
        "mechanic": "Puts an intuitive read into words at the moment it "
                    "arrives. Gate 57 hears it, gate 20 says it before it is "
                    "reasoned away.",
        "transit_gift": "You can name what is off about a situation while it "
                        "is still useful to name it.",
        "good_for": ["speaking up in the meeting rather than after it",
                     "naming the thing everyone is avoiding",
                     "acting on a first read"],
        "difficulty": "Delivered without the pause that would soften it. What "
                      "is accurate is not automatically welcome, and this "
                      "channel does not check first.",
    },

    (21, 45): {
        "name": "Control of Resources",
        "mechanic": "Takes charge of material things and states the claim out "
                    "loud. Gate 21 controls the territory, gate 45 speaks for "
                    "the group that holds it.",
        "transit_gift": "Willpower applied to money, assets and territory, "
                        "with the authority to say so.",
        "good_for": ["money decisions, budgets, pricing, invoicing",
                     "claiming ownership of a project or a domain",
                     "the conversation about who is responsible for what"],
        "difficulty": "Willpower runs on a real battery through the Heart "
                      "centre and it empties. Control asserted here has to be "
                      "maintained after the window, by you, on your own energy.",
    },

    (23, 43): {
        "name": "Insight Made Sayable",
        "mechanic": "Translates an individual, non-obvious knowing into "
                    "language other people can parse. Gate 43 knows it "
                    "strangely, gate 23 finds the plain words.",
        "transit_gift": "The idea you cannot normally explain becomes "
                        "explicable. Genius and being misunderstood run through "
                        "the same wire, and this is the day the wire works.",
        "good_for": ["explaining the thing you keep failing to explain",
                     "writing down an insight in full",
                     "a conversation with someone who has not been following"],
        "difficulty": "Timing is not included. This channel supplies the words "
                      "and no sense of whether anyone asked. Unsolicited "
                      "brilliance still lands as an interruption.",
    },

    (24, 61): {
        "name": "The Return of a Question",
        "mechanic": "Cycles an unknown until a rationalisation forms. Gate 61 "
                    "is pressure to know, gate 24 returns to the same question "
                    "again and again until something resolves.",
        "transit_gift": "The mental loop stops being circular and produces a "
                        "usable formulation.",
        "good_for": ["sitting with the question rather than escaping it",
                     "writing until the thought completes",
                     "returning deliberately to an unfinished problem"],
        "difficulty": "This is inspiration pressure and it has no off switch. "
                      "It can present as insomnia and rumination if there is "
                      "nothing to point it at.",
    },

    (25, 51): {
        "name": "Shock and What Survives It",
        "mechanic": "Runs competitive, initiating force through the sense of "
                    "self. Gate 51 shocks, gate 25 meets it with an "
                    "impersonal, undiminished love of being alive.",
        "transit_gift": "Resilience. The capacity to take a hit and not "
                        "contract around it.",
        "good_for": ["doing the thing that scares you",
                     "competing, entering, putting yourself forward",
                     "recovering from something that knocked you"],
        "difficulty": "It works by shock, so it usually arrives as an event "
                      "you did not choose. This is the channel of the "
                      "initiate, and initiation is not comfortable.",
    },

    (26, 44): {
        "name": "The Persuasive Past",
        "mechanic": "Uses memory and pattern to sell something. Gate 44 "
                    "recognises the pattern from before, gate 26 makes the "
                    "case with it.",
        "transit_gift": "You can use your own history as evidence. Track "
                        "record becomes a usable argument.",
        "good_for": ["the pitch built on what you have already done",
                     "negotiating from precedent",
                     "recognising you have been here before"],
        "difficulty": "Gate 26's shadow is the useful exaggeration. The line "
                      "between confident framing and a story that is not quite "
                      "true is thinner on this window than it feels.",
    },

    (27, 50): {
        "name": "Care and Its Rules",
        "mechanic": "Feeds and protects, and sets the terms that make it "
                    "sustainable. Gate 27 provides the care, gate 50 holds the "
                    "values that stop it becoming ruinous.",
        "transit_gift": "Capacity to look after someone or something properly, "
                        "with limits attached.",
        "good_for": ["caring for a person, animal, project or body",
                     "cooking, feeding, tending, repairing",
                     "deciding what you are and are not responsible for"],
        "difficulty": "Its shadow is over-responsibility. On these days you "
                      "will be able to take on more than is yours, and it will "
                      "feel virtuous while you do it.",
    },

    (28, 38): {
        "name": "The Fight Worth Having",
        "mechanic": "Applies stubborn opposition to a search for meaning. Gate "
                    "38 fights, gate 28 asks whether this particular fight is "
                    "worth a life.",
        "transit_gift": "Willingness to struggle on purpose, plus some read on "
                        "whether the struggle is the right one.",
        "good_for": ["persisting with something genuinely hard",
                     "deciding to stop fighting something that is not worth it",
                     "work that only yields to sustained pressure"],
        "difficulty": "This channel finds meaning through struggle and will "
                      "manufacture struggle if none is available. Give it a "
                      "real obstacle or it will pick one.",
    },

    (29, 46): {
        "name": "Saying Yes With the Body",
        "mechanic": "Commits to an experience and gives the body to it. Gate "
                    "29 says yes, gate 46 turns up in a physical form that can "
                    "actually carry it.",
        "transit_gift": "The ability to commit and be present for what you "
                        "committed to. Being in the right place is the whole "
                        "mechanic.",
        "good_for": ["saying yes to something you would normally decline",
                     "showing up in person",
                     "physical practice, movement, being in your body"],
        "difficulty": "Gate 29 says yes indiscriminately. The commitment "
                      "outlasts the window by a long way, so the yes you give "
                      "on this day is one you keep on ordinary days.",
    },

    (30, 41): {
        "name": "Desire and the Fantasy of It",
        "mechanic": "Starts a new emotional cycle from pure appetite. Gate 41 "
                    "is the pressure to begin feeling something new, gate 30 "
                    "is the intensity of wanting it.",
        "transit_gift": "Access to what you actually want, before it gets "
                        "edited into what is reasonable.",
        "good_for": ["naming the want without committing to it",
                     "starting something for the appetite rather than the plan",
                     "noticing which fantasies keep returning"],
        "difficulty": "This is fantasy pressure and it is emotional, so it is "
                      "at its least reliable at its most convincing. Write the "
                      "want down. Decide about it on a different day.",
    },

    (32, 54): {
        "name": "Ambition and Its Odds",
        "mechanic": "Drives to rise, and checks whether this particular attempt "
                    "will survive. Gate 54 supplies the ambition, gate 32 "
                    "assesses what is worth continuing.",
        "transit_gift": "Ambition with a filter on it. You can want to advance "
                        "and still tell which route is viable.",
        "good_for": ["assessing an opportunity you are drawn to",
                     "the practical steps of advancement, applications, asks",
                     "deciding what to abandon"],
        "difficulty": "Gate 32's shadow is fear of failure, and it does not "
                      "read as fear, it reads as prudence. Notice whether the "
                      "assessment is analysis or avoidance.",
    },

    (34, 57): {
        "name": "Power Guided by Instinct",
        "mechanic": "Puts raw available force behind an intuitive read. Gate 34 "
                    "supplies the power, gate 57 tells it which way is safe.",
        "transit_gift": "Force and instinct in the same moment, which is rare. "
                        "You can move decisively and correctly at once.",
        "good_for": ["acting fast on something you sense is right",
                     "physical work requiring judgement, not just effort",
                     "getting out of a situation quickly"],
        "difficulty": "The power is louder than the instinct. If you are "
                      "borrowing gate 34, the risk is spending the force and "
                      "missing the quiet signal that was supposed to aim it.",
    },

    (35, 36): {
        "name": "Appetite for the Untried",
        "mechanic": "Moves through emotional experience for the sake of having "
                    "had it. Gate 36 hungers for the new, gate 35 has been "
                    "through enough to say what it was like.",
        "transit_gift": "Progress through novelty. Access to the next "
                        "experience rather than the next repetition.",
        "good_for": ["doing something you have never done",
                     "changing a context that has gone flat",
                     "travel, new rooms, new people"],
        "difficulty": "Emotional, and it produces crisis as readily as growth. "
                      "The shadow here is a life of many experiences and no "
                      "accumulation. Novelty on the window, integration after.",
    },

    (37, 40): {
        "name": "The Bargain",
        "mechanic": "Sets the deal at the centre of every relationship: what is "
                    "given and what is owed. Gate 37 offers loyalty and "
                    "affection, gate 40 supplies the work and expects "
                    "recognition for it.",
        "transit_gift": "Clarity about the actual terms of a relationship, "
                        "work arrangement or family role.",
        "good_for": ["naming what you give and what you get",
                     "repairing an agreement that has drifted",
                     "asking to be recognised for work already done"],
        "difficulty": "Gate 40 needs real rest and will not admit it. The "
                      "bargain becomes visible on these days precisely because "
                      "one side of it has been quietly failing.",
    },

    (39, 55): {
        "name": "Provocation and Mood",
        "mechanic": "Pokes at emotional state to find out what is real. Gate 39 "
                    "provokes, gate 55 holds a mood whose fullness or emptiness "
                    "is entirely its own business.",
        "transit_gift": "Access to your own emotional truth, and to what "
                        "provokes it. Creative material comes out of this.",
        "good_for": ["creative work with feeling in it",
                     "noticing what actually moves you",
                     "letting a mood be what it is without fixing it"],
        "difficulty": "Provocation aimed at people is still provocation. This "
                      "channel is capable of starting a fight to find out "
                      "whether someone cares, and it usually works, badly.",
    },

    (42, 53): {
        "name": "Finishing What Was Started",
        "mechanic": "Runs a cycle from beginning to completion. Gate 53 starts, "
                    "gate 42 sees it through the middle and out the far end.",
        "transit_gift": "Completion energy. The thing at eighty percent can "
                        "reach a hundred.",
        "good_for": ["finishing the nearly-done project",
                     "closing out, shipping, submitting, filing",
                     "ending a cycle deliberately rather than letting it lapse"],
        "difficulty": "Gate 53's pressure starts things whether or not the "
                      "previous thing finished. Point this at completion, not "
                      "at yet another beginning, or you accumulate open cycles.",
    },

    (47, 64): {
        "name": "Making Sense of the Past",
        "mechanic": "Processes a confusion of images until meaning resolves. "
                    "Gate 64 holds the unsorted material, gate 47 works it into "
                    "an account that makes sense.",
        "transit_gift": "Something confusing from your own past becomes "
                        "legible. Not resolved, but understood.",
        "good_for": ["reviewing something you never made sense of",
                     "therapy, journalling, deliberate reflection",
                     "letting a confusion sit rather than forcing a conclusion"],
        "difficulty": "This is mental pressure and it cannot be hurried. "
                      "Forcing a conclusion produces a tidy story that is not "
                      "true. If it does not resolve inside the window, that is "
                      "the mechanic working, not failing.",
    },
}


# ---------------------------------------------------------------------------
# Gates.
#
# `theme` is what the gate does. `hanging` is the one that matters for a
# calendar: what it is like to carry this gate with the other half of its
# channel undefined. A hanging gate is a standing open question. It gets
# answered by a person who carries the other half, or by a transit, and by
# nothing else. Place and environment do not define a channel.
# ---------------------------------------------------------------------------

GATE_MEANINGS: dict[int, dict] = {
    1:  {"theme": "Creative material that originates with you and nobody else.",
         "hanging": "You produce, and have no native mechanism for putting it in front of anyone. You wait on someone or something to make the case for the work."},
    2:  {"theme": "Knowing which direction is yours before knowing why.",
         "hanging": "You can feel where you are pointed and have no engine attached to it. You are waiting on power, not on clarity."},
    3:  {"theme": "The first ordered step out of confusion.",
         "hanging": "You have starts in you that never get past the start. You wait on something to hold the limit steady enough to build inside."},
    4:  {"theme": "Offering a formula that would answer a doubt.",
         "hanging": "You produce answers with no question attached, and no test. You wait on someone to supply the doubt worth answering."},
    5:  {"theme": "Holding a fixed rhythm.",
         "hanging": "You keep the pattern rigidly and cannot flex it. You wait on something to stretch the routine without breaking it."},
    6:  {"theme": "Deciding when to let someone close.",
         "hanging": "You open and close without a steady read on the barrier itself. You wait on something to do the actual work of getting through."},
    7:  {"theme": "Seeing the route the group should take.",
         "hanging": "You see where it should go and cannot say it as influence. You wait on someone to give the direction a voice people follow."},
    8:  {"theme": "Making the case for something worth contributing.",
         "hanging": "You can advocate, and have no material of your own to advocate for. You wait on something original to represent."},
    9:  {"theme": "Focus applied to detail.",
         "hanging": "You can concentrate on small things without knowing which small thing. You wait on stillness to settle you onto one."},
    10: {"theme": "How you conduct yourself, as an expression of self.",
         "hanging": "You know how you should behave and cannot reliably get it into the room. You wait on presence, on power, or on instinct to carry it."},
    11: {"theme": "Collecting ideas worth holding.",
         "hanging": "Ideas accumulate and none of them go anywhere. You wait on a way to tell them that makes anyone listen."},
    12: {"theme": "Articulation that only arrives when the mood allows it.",
         "hanging": "You have the words some days and not others, with no control over which. You wait on openness to another person to unlock the timing."},
    13: {"theme": "Receiving what other people confide.",
         "hanging": "You take in a great deal and it stays in. You wait on the retreat that turns what you gathered into something you can tell back."},
    14: {"theme": "Power and material resource directed at what you value.",
         "hanging": "You have fuel and no settled direction to spend it on. You wait on something to point it."},
    15: {"theme": "Tolerance for a wide range of human rhythms.",
         "hanging": "Your range is extreme and has no floor under it. You wait on a beat to make the variation into something sustainable."},
    16: {"theme": "Enthusiasm that commits to the attempt.",
         "hanging": "You leap without depth behind it. You wait on skill built over time to make the leap land."},
    17: {"theme": "Having a point of view.",
         "hanging": "You hold opinions with nothing to back them. You wait on the details that would turn a position into an argument."},
    18: {"theme": "Seeing precisely what is wrong with a pattern.",
         "hanging": "You see the flaw and get no satisfaction from it. You wait on the appetite that would make correcting it feel good rather than sour."},
    19: {"theme": "Sensing what is needed, materially and emotionally.",
         "hanging": "You feel the need acutely with no read on the terms. You wait on something to decide whether the arrangement is acceptable."},
    20: {"theme": "The present moment, spoken.",
         "hanging": "You are here now and have nothing pushing through. You wait on power, on instinct or on self-knowledge to give the moment content."},
    21: {"theme": "Control over your own material territory.",
         "hanging": "You want control and cannot get the claim into words. You wait on a voice that speaks for the group you are trying to lead."},
    22: {"theme": "Emotional openness to another person.",
         "hanging": "You open and have no words for what you opened about. You wait on articulation to arrive with the mood."},
    23: {"theme": "Putting the strange knowing into plain language.",
         "hanging": "You can explain, and have nothing peculiar enough to need explaining. You wait on the insight itself."},
    24: {"theme": "Returning to the same question until it resolves.",
         "hanging": "You return and return with no pressure driving it anywhere. You wait on the not-knowing that makes the return productive."},
    25: {"theme": "Impersonal love of being alive, indiscriminate and whole.",
         "hanging": "You hold the innocence and it never gets tested. You wait on a shock to prove it is real."},
    26: {"theme": "Making the persuasive case from what has already happened.",
         "hanging": "You can sell, with no pattern underneath the pitch. You wait on the recognition of what actually worked before."},
    27: {"theme": "Care, feeding, protection of others.",
         "hanging": "You give care with no limit on it. You wait on values to tell you where your responsibility ends."},
    28: {"theme": "Asking whether this struggle is worth a life.",
         "hanging": "You question the purpose and have no fight in you. You wait on something stubborn enough to test the question against."},
    29: {"theme": "Committing, fully, to an experience.",
         "hanging": "You say yes with no read on whether you should be there. You wait on the sense of being in the right place."},
    30: {"theme": "The intensity of wanting.",
         "hanging": "Desire runs hot with nothing initiating a new cycle. You wait on the pressure that turns wanting into a beginning."},
    31: {"theme": "Speaking a direction others will follow.",
         "hanging": "You can lead by voice with no route of your own to name. You wait on someone who actually sees where to go."},
    32: {"theme": "Judging what will endure and what will not.",
         "hanging": "You assess continuously with nothing driving you upward. You wait on ambition to make the assessment worth making."},
    33: {"theme": "Withdrawing, then telling what the experience was.",
         "hanging": "You retreat and come back with nothing gathered. You wait on the material other people confide in you."},
    34: {"theme": "Raw available power, answerable to nothing.",
         "hanging": "You have force and no channel for it, which reads as restlessness or as being busy with nothing. You wait on something to aim it: presence, instinct, or a sense of self."},
    35: {"theme": "Having been through it, and being able to say so.",
         "hanging": "You have the experience and no hunger for the next one. You wait on appetite to move you on."},
    36: {"theme": "Hunger for emotional experience you have not had yet.",
         "hanging": "You crave the new with no capacity to metabolise it into progress. You wait on something to turn the crisis into a story."},
    37: {"theme": "Loyalty, affection, the offer of belonging.",
         "hanging": "You give warmth and the bargain never gets stated. You wait on someone to name the work and the recognition owed."},
    38: {"theme": "Stubborn opposition for its own sake.",
         "hanging": "You fight without knowing what for. You wait on the question of whether this particular struggle has a purpose."},
    39: {"theme": "Provoking to find out what is real.",
         "hanging": "You provoke and get no read on what you surfaced. You wait on the mood that would give the provocation meaning."},
    40: {"theme": "The work delivered, and the recognition expected for it.",
         "hanging": "You deliver and no one names the arrangement. You wait on the loyalty side of the bargain to be offered."},
    41: {"theme": "Pressure to begin feeling something new.",
         "hanging": "The pressure builds with no intensity to carry it. You wait on desire to give the new cycle its heat."},
    42: {"theme": "Seeing a cycle through to its actual end.",
         "hanging": "You can finish and nothing has started. You wait on the pressure that begins things."},
    43: {"theme": "Knowing something in a way that makes no sense to anyone.",
         "hanging": "You know it and cannot say it, which is the most isolating of the hanging gates. You wait on the plain words that would let it out."},
    44: {"theme": "Recognising the pattern from before, in people and situations.",
         "hanging": "You recognise and cannot make anything of the recognition. You wait on someone to build the case out of it."},
    45: {"theme": "Speaking for the group about what it holds.",
         "hanging": "You can speak for the resource and do not control it. You wait on the willpower that would make the claim real."},
    46: {"theme": "The body in the right place at the right time.",
         "hanging": "You turn up and nothing has been committed to. You wait on the yes."},
    47: {"theme": "Working a confusion into an account that makes sense.",
         "hanging": "You process and have nothing unresolved enough to need it. You wait on the raw confusing material."},
    48: {"theme": "Depth of skill and knowledge, accumulated slowly.",
         "hanging": "You have depth and never risk using it, which surfaces as a fear of not being ready. You wait on the enthusiasm that would make you attempt it anyway."},
    49: {"theme": "Setting the conditions, and breaking the deal over them.",
         "hanging": "You hold principles with no sense of what anyone actually needs. You wait on the reading of need to give the conditions something to be about."},
    50: {"theme": "The values that keep a group from destroying itself.",
         "hanging": "You hold the rules and have nothing to apply them to. You wait on the caring that gives values a subject."},
    51: {"theme": "Shock, competition, going first.",
         "hanging": "You shock and it is not in service of anything. You wait on the sense of self that would make the shock initiatory rather than just disruptive."},
    52: {"theme": "Stillness. Not moving, on purpose.",
         "hanging": "You are still and it goes nowhere. You wait on the focus that would spend the stillness on something."},
    53: {"theme": "Pressure to begin.",
         "hanging": "You start constantly and finish nothing, and the open cycles accumulate. You wait on the capacity to see one through."},
    54: {"theme": "Ambition. The drive to rise from where you started.",
         "hanging": "You push upward with no read on which route survives. You wait on the judgement that would tell you what is worth continuing."},
    55: {"theme": "A mood whose fullness or emptiness answers to nothing.",
         "hanging": "The mood arrives and departs with nothing to test it against. You wait on the provocation that would show you what it is made of."},
    56: {"theme": "Telling it as a story people will stay for.",
         "hanging": "You can tell, and have no ideas of your own to tell about. You wait on the idea worth the telling."},
    57: {"theme": "Instinctive clarity, in the moment, about what is safe.",
         "hanging": "You hear it once, quietly, and nothing acts on it. You wait on power, presence or conduct to convert the signal into a move."},
    58: {"theme": "The appetite for making things better.",
         "hanging": "You are full of vitality with nothing to improve. You wait on the eye that spots what is actually wrong."},
    59: {"theme": "Working through another person's barrier to real intimacy.",
         "hanging": "You get through and have no read on when you should. You wait on the judgement that decides who is let in."},
    60: {"theme": "Accepting a limit as the actual shape of the situation.",
         "hanging": "You accept the constraint and nothing new comes out of it. You wait on the first step that would make the limit generative."},
    61: {"theme": "Pressure to know what cannot be known.",
         "hanging": "The pressure builds with no question to spend it on, which is where insomnia and rumination live. You wait on a specific unknown to return to."},
    62: {"theme": "Detail, names, facts, the record.",
         "hanging": "You accumulate detail with no position it supports. You wait on an opinion for the facts to be evidence for."},
    63: {"theme": "Doubt about whether the pattern holds.",
         "hanging": "You doubt with no formula to test against, which is doubt that never resolves. You wait on an answer worth checking."},
    64: {"theme": "A confusion of images that has not sorted itself yet.",
         "hanging": "The material churns and never resolves into anything. You wait on the processing that would make sense of it."},
}


# ---------------------------------------------------------------------------
# Accessors. Centres and gate names are derived, never restated, so this file
# cannot drift away from hd_tables.py.
# ---------------------------------------------------------------------------
def channel_key(gate_a: int, gate_b: int) -> tuple[int, int]:
    return (min(gate_a, gate_b), max(gate_a, gate_b))


def describe_channel(gate_a: int, gate_b: int, held_gate: int = None) -> dict:
    """
    Full description of a channel. If `held_gate` is given it is the gate the
    person carries natally, so the other half is the one a transit supplied,
    and the hanging text for the held gate explains the standing condition
    this window is temporarily answering.
    """
    key = channel_key(gate_a, gate_b)
    m = CHANNEL_MEANINGS[key]
    lo, hi = key
    out = {
        "channel": f"{lo}-{hi}",
        "name": m["name"],
        "centers": sorted({GATE_CENTER[lo], GATE_CENTER[hi]}),
        "gates": {
            lo: {"name": GATE_NAMES[lo], "center": GATE_CENTER[lo],
                 **GATE_MEANINGS[lo]},
            hi: {"name": GATE_NAMES[hi], "center": GATE_CENTER[hi],
                 **GATE_MEANINGS[hi]},
        },
        "mechanic": m["mechanic"],
        "transit_gift": m["transit_gift"],
        "good_for": list(m["good_for"]),
        "difficulty": m["difficulty"],
    }
    if held_gate is not None:
        supplied = hi if held_gate == lo else lo
        out["held_gate"] = held_gate
        out["supplied_gate"] = supplied
        out["standing_condition"] = GATE_MEANINGS[held_gate]["hanging"]
    return out


def validate() -> list[str]:
    """
    Every channel in hd_tables has copy, every gate 1 to 64 has copy, and no
    key here describes a channel that does not exist. Returns a list of
    problems, empty when clean, so a test or a build gate can assert on it.
    """
    problems = []
    canonical = {channel_key(a, b) for a, b in CHANNELS}
    for missing in sorted(canonical - set(CHANNEL_MEANINGS)):
        problems.append(f"channel {missing} has no meaning entry")
    for extra in sorted(set(CHANNEL_MEANINGS) - canonical):
        problems.append(f"meaning entry {extra} is not a real channel")
    for g in range(1, 65):
        if g not in GATE_MEANINGS:
            problems.append(f"gate {g} has no meaning entry")
        if g not in GATE_NAMES:
            problems.append(f"gate {g} has no classical name")
    required = {"name", "mechanic", "transit_gift", "good_for", "difficulty"}
    for key, m in CHANNEL_MEANINGS.items():
        for field in sorted(required - set(m)):
            problems.append(f"channel {key} missing field {field}")
        if not m.get("good_for"):
            problems.append(f"channel {key} has an empty good_for list")
    for g, m in GATE_MEANINGS.items():
        for field in sorted({"theme", "hanging"} - set(m)):
            problems.append(f"gate {g} missing field {field}")
    # House style is not decoration here: em dashes are banned in ZDA copy and
    # this is the only place that can catch a reintroduced one at build time.
    for label, table in (("channel", CHANNEL_MEANINGS), ("gate", GATE_MEANINGS)):
        for key, m in table.items():
            if "—" in repr(m):
                problems.append(f"{label} {key} contains an em dash")
    return problems
