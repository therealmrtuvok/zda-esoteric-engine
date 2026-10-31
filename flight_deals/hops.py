"""Hop trips: two separate tickets that together get you somewhere for less.

1. home -> hub, round trip for the whole stay (e.g. Toronto -> Medellín, or
   Toronto -> Miami just to position for a cheaper international flight), and
2. hub -> destination, round trip inside that stay (e.g. Medellín -> Cusco, or
   Miami -> Rio).

Each [[hops]] group in config.toml is one such pattern. Both tickets are priced
(Google Flights and/or Travelpayouts), added up, and compared with flying to
the same place directly from home.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import google_flights
import travelpayouts
from common import Finding, Hops, Origin, Region, Trip


def leg_dates(group: Hops, out: date, back: date) -> tuple[date, date]:
    return out + timedelta(days=group.out_offset_days), back - timedelta(days=group.back_offset_days)


def todays_group(groups: list[Hops], trip: Trip, today: date) -> Hops | None:
    """Which group gets today's one Google Flights hop search.

    Date pairs rotate daily too, so step groups every len(google_trips) days;
    otherwise each group would always land on the same date pair.
    """
    if not groups:
        return None
    step = max(1, len(trip.google_trips))
    return groups[(today.toordinal() // step) % len(groups)]


def _tp_city(group: Hops, airport: str) -> str:
    return group.tp_cities.get(airport, airport)


def _airport(group: Hops, code: str) -> str:
    """Travelpayouts city code (NYC) -> the hub airport it stands for (JFK)."""
    back = {city: ap for ap, city in group.tp_cities.items()}
    return back.get(code, code)


def _as_legs(found: list[Finding], group: Hops) -> list[Finding]:
    for f in found:
        f.leg, f.is_deal, f.reasons = True, False, []
        f.origin = group.hubs.get(f.from_code, f.from_code)
        f.key = f"leg|{group.name}|" + f.key
    return found


def google_legs(trip: Trip, group: Hops, out: date, back: date, api_key: str) -> list[Finding]:
    """One search: every hub to every onward airport, inside the trip."""
    leg_out, leg_back = leg_dates(group, out, back)
    hub = Origin(name="hub", airports=",".join(group.hubs), city="")
    onward = Region(name=group.name, deal_price=0, airports=group.onward)
    return _as_legs(google_flights.search(trip, hub, onward, leg_out, leg_back, api_key), group)


def _rows_to_legs(rows: list[dict], keep, make) -> list[Finding]:
    """Cheapest row per (destination, dates) that `keep` accepts, turned into legs."""
    cheapest: dict[tuple, dict] = {}
    for row in rows:
        try:
            out = date.fromisoformat(row["departure_at"][:10])
            back = date.fromisoformat(row["return_at"][:10])
            price = float(row["price"])
        except (KeyError, TypeError, ValueError):
            continue
        dest = row.get("destination", "")
        if not keep(dest, out, back):
            continue
        k = (dest, out, back)
        if k not in cheapest or price < cheapest[k]["_price"]:
            cheapest[k] = {**row, "_price": price, "_out": out, "_back": back}
    return [make(dest, out, back, row) for (dest, out, back), row in cheapest.items()]


def travelpayouts_first_legs(trip: Trip, group: Hops, origin: Origin, rows: list[dict]) -> list[Finding]:
    """home -> hub fares from the home rows already fetched (e.g. Toronto -> Miami)."""
    hub_cities = {_tp_city(group, h) for h in group.hubs}

    def make(dest, out, back, row):
        hub = _airport(group, dest)
        link = row.get("link")
        return Finding(
            key=f"leg|{group.name}|tp1|{origin.name}|{hub}|{out}|{back}", source=travelpayouts.SOURCE,
            origin=origin.name, kind="fare", place=f"{group.hubs[hub]} ({hub})", expires=out,
            price=row["_price"], depart=out, ret=back, details=f"{row.get('airline', '?')}",
            url=f"https://www.aviasales.com{link}" if link else None, extra_cost=origin.extra_cost,
            from_code=origin.city, dest_code=hub, leg=True)
    return _rows_to_legs(rows, lambda d, o, b: d in hub_cities and trip.fits(o, b), make)


def travelpayouts_legs(trip: Trip, group: Hops, token: str,
                       cities: dict[str, tuple[str, str]]) -> tuple[list[Finding], list[str]]:
    """Recently seen hub -> onward fares (free). Returns legs and per-hub errors."""
    onward = {c.strip() for c in group.onward.split(",")} | set(group.onward_cities)
    legs, errors = [], []
    for hub, name in group.hubs.items():
        try:
            rows = travelpayouts.fetch_prices(trip, Origin(name=name, airports=hub, city=_tp_city(group, hub)), token)
        except Exception as e:
            errors.append(f"Travelpayouts {name}: {e}")
            continue

        def make(dest, out, back, row, hub=hub, name=name):
            link = row.get("link")
            return Finding(
                key=f"leg|{group.name}|tp|{hub}|{dest}|{out}|{back}", source=travelpayouts.SOURCE, origin=name,
                kind="fare", place=f"{cities.get(dest, (dest, ''))[0]} ({dest})", expires=out,
                price=row["_price"], depart=out, ret=back, details=f"{row.get('airline', '?')}",
                url=f"https://www.aviasales.com{link}" if link else None,
                from_code=hub, dest_code=dest, leg=True)
        legs += _rows_to_legs(rows, lambda d, o, b: d in onward and trip.depart[0] <= o <= b <= trip.ret[1], make)
    return legs, errors


def combine(trip: Trip, group: Hops, findings: list[Finding]) -> list[Finding]:
    """Pair each home -> hub fare with each hub -> onward fare that fits inside it."""
    def money(p: float) -> str:
        return f"{trip.currency} {p:,.0f}"

    def span(f: Finding) -> str:
        return f"{f.depart:%b %d} to {f.ret:%b %d}"

    def brief(f: Finding) -> str:
        """Airline and stops, without the 'From XXX.' prefix (the line already says where from)."""
        return re.sub(r"^From \S+\. ", "", f.details.splitlines()[0])

    homes = {o.name for o in trip.origins}
    out_gap, back_gap = timedelta(days=group.out_offset_days), timedelta(days=group.back_offset_days)
    fares = [f for f in findings if f.kind == "fare" and f.price is not None and f.depart and f.ret]
    first = [f for f in fares if f.origin in homes and _airport(group, f.dest_code) in group.hubs]
    second = [f for f in fares if f.leg and f.from_code in group.hubs and f.origin not in homes]
    direct: dict[tuple[str, str], Finding] = {}
    for f in fares:
        if not f.leg and f.origin in homes:
            k = (f.origin, f.dest_code)
            if k not in direct or f.price < direct[k].price:
                direct[k] = f

    best: dict[tuple[str, str], tuple[Finding, Finding]] = {}
    for a in first:
        hub = _airport(group, a.dest_code)
        for b in second:
            if b.from_code != hub or not (b.depart >= a.depart + out_gap and b.ret <= a.ret - back_gap):
                continue
            k = (a.origin, b.dest_code)
            if k not in best or a.price + b.price < sum(x.price for x in best[k]):
                best[k] = (a, b)

    combos = []
    for (origin, dest), (a, b) in best.items():
        hub_code = _airport(group, a.dest_code)
        hub = group.hubs[hub_code]
        total = a.price + b.price
        lines = [
            f"1) {origin} to {hub}, {span(a)}: {money(a.price)} ({a.source}; {brief(a)})",
            f"2) {hub} to {b.place}, {span(b)}: {money(b.price)} ({b.source}; {brief(b)})",
        ]
        reasons = []
        if total + a.extra_cost <= group.deal_price:
            reasons.append(f"both tickets together under {money(group.deal_price)}")
        d = direct.get((origin, dest))
        if d:
            saving = d.price - total
            lines.append(f"Flying {origin} to {dest} directly instead: {money(d.price)}"
                         + (f" (the hop saves {money(saving)})" if saving > 0 else " (direct is cheaper)"))
            if total <= d.price * (1 - group.min_saving_pct / 100):
                reasons.append(f"saves {saving / d.price:.0%} over flying there directly")
        lines.append("Two separate tickets: a delay on one won't be covered by the other, so leave a buffer.")
        if b.url:
            lines.append(f"Second ticket: {b.url}")
        combos.append(Finding(
            key=f"hop|{group.name}|{origin}|{hub_code}|{dest}|{a.depart}|{a.ret}",
            source=a.source if a.source == b.source else f"{a.source} + {b.source}",
            origin=origin, kind="fare", place=f"{b.place} via {hub}", region=group.name,
            price=total, extra_cost=a.extra_cost, depart=a.depart, ret=a.ret,
            details="\n".join(lines), url=a.url, from_code=a.from_code, dest_code=dest,
            is_deal=bool(reasons), reasons=reasons, expires=a.depart))
    return sorted(combos, key=lambda f: f.price)
