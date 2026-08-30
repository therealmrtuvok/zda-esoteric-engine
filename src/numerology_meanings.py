"""
Personal month and personal day meaning tables for the energy calendar.

interpretations.py already covers life path and personal year. This adds the
two shorter cycles, which are what a daily calendar actually runs on.

Master numbers are included deliberately. reduce() keeps 11, 22 and 33, so
personal_day() genuinely returns them and a table of 1 to 9 would produce
either a KeyError or, worse, an empty string that reads as "no meaning today".
validate() proves the coverage by enumeration rather than by assertion.
"""

from datetime import date, timedelta

from .interpretations import PERSONAL_YEARS
from .numerology import personal_day, personal_month, personal_year

PERSONAL_MONTHS: dict[int, str] = {
    1:  "Start the month's work in the first week. What you initiate here is "
        "what the month ends up being about.",
    2:  "Cooperative and slow. Progress comes through other people, which "
        "means it arrives on their timing rather than yours.",
    3:  "Visible and social. A good month to publish, present and be seen. "
        "Scattered if you do not pick a target.",
    4:  "Structural. Admin, systems, foundations, the unglamorous middle. "
        "Nothing launches cleanly this month and that is not a problem.",
    5:  "Loose and mobile. Keep the calendar flexible. Commitments made this "
        "month tend to need renegotiating.",
    6:  "Responsibility and home. Care work surfaces, invited or not. The "
        "month asks what is actually yours to carry.",
    7:  "Inward. Study, review, rest. A poor month for pushing an outcome and "
        "a good one for understanding why the last one went the way it did.",
    8:  "Material. Money, authority and results come due. The month rewards "
        "having already done the work rather than starting it.",
    9:  "Closing. Finish, clear, release. Starting something new this month "
        "tends to mean carrying it through a cycle that is already ending.",
    11: "A 2 month with more exposure. Intuitive and thin-skinned. Useful for "
        "sensing what is going on, hard for holding a boundary.",
    22: "A 4 month with a longer horizon. Build the thing properly rather "
        "than the version that gets you through the quarter.",
    33: "A 6 month turned outward. Care at a scale beyond your own household. "
        "The risk is spending yourself on people who did not ask.",
}

PERSONAL_DAYS: dict[int, str] = {
    1:  "Initiating. Best day of the cycle to start, decide or go first. "
        "Poor day for waiting on consensus.",
    2:  "Receptive and slow. Wait, collaborate, let something develop. "
        "Pushing today usually costs more than it gains.",
    3:  "Expressive. Talk, write, publish, socialise. Scatters easily, so "
        "give it one thing to be expressive about.",
    4:  "Grind. Admin, detail, structure, the boring necessary pass. Low "
        "inspiration and high usefulness.",
    5:  "Unstable and interesting. Change, movement, the unplanned. A bad day "
        "to sign something and a good one to explore.",
    6:  "Domestic and relational. Care, home, obligation. Attend to the "
        "person or thing that has been waiting.",
    7:  "Quiet. Research, reflect, rest. Withdrawing today is the correct "
        "use of it, not an avoidance of it.",
    8:  "Transactional. Money, negotiation, authority, results. Ask for the "
        "thing. Send the invoice.",
    9:  "Completion and release. Finish, clear, end, let go. Starting here "
        "means starting at the bottom of a cycle.",
    11: "A 2 day with the signal turned up. Highly intuitive, highly porous. "
        "Trust the read and protect the boundary.",
    22: "A 4 day pointed at something that matters. Structural work with a "
        "long payoff. Do the version you will not have to redo.",
    33: "A 6 day at full reach. Care given generously. Watch the line between "
        "generous and depleted, because it does not announce itself.",
}


def day_numbers(birth: date, on: date) -> dict:
    """The three running cycles for one date, with their text attached."""
    py = personal_year(birth, on)
    pm = personal_month(birth, on)
    pd = personal_day(birth, on)
    return {
        "personal_year": py,
        "personal_month": pm,
        "personal_day": pd,
        "personal_year_text": PERSONAL_YEARS[py],
        "personal_month_text": PERSONAL_MONTHS[pm],
        "personal_day_text": PERSONAL_DAYS[pd],
    }


def validate(sample_years: int = 12) -> list[str]:
    """
    Prove coverage by enumeration: walk a wide spread of birth dates over a
    long date range, collect every personal month and day value that actually
    occurs, and report any the tables do not cover.
    """
    problems = []
    seen_month, seen_day = set(), set()
    for month in range(1, 13):
        for dom in (1, 7, 16, 28):
            try:
                birth = date(1994, month, dom)
            except ValueError:
                continue
            on = date(2024, 1, 1)
            for _ in range(sample_years * 365):
                seen_month.add(personal_month(birth, on))
                seen_day.add(personal_day(birth, on))
                on += timedelta(days=1)
    seen_year = set()
    for month in range(1, 13):
        for dom in (1, 7, 16, 28):
            try:
                birth = date(1994, month, dom)
            except ValueError:
                continue
            for y in range(2020, 2020 + sample_years):
                seen_year.add(personal_year(birth, date(y, 12, 1)))
                seen_year.add(personal_year(birth, date(y, 1, 1)))
    for v in sorted(seen_year - set(PERSONAL_YEARS)):
        problems.append(f"personal year {v} occurs but has no text")
    for v in sorted(seen_month - set(PERSONAL_MONTHS)):
        problems.append(f"personal month {v} occurs but has no text")
    for v in sorted(seen_day - set(PERSONAL_DAYS)):
        problems.append(f"personal day {v} occurs but has no text")
    for label, table in (("month", PERSONAL_MONTHS), ("day", PERSONAL_DAYS)):
        for k, text in table.items():
            if "—" in text:
                problems.append(f"personal {label} {k} contains an em dash")
    return problems
