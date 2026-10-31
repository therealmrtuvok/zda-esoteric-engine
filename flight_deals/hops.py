"""Hop trips: fly home -> hub (e.g. Medellín) round trip, then a separate round
trip hub -> somewhere else in Latin America in the middle of your stay.

Both tickets are priced (Google Flights and/or Travelpayouts), added up, and
compared with flying to the same place directly from home.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import google_flights
import travelpayouts
from common import Finding, Hops, Origin, Region, Trip

REGION = "Hop via Colombia"


def leg_dates(hops: Hops, out: date, back: date) -> tuple[date, date]:
    return out + timedelta(days=hops.out_offset_days), back - timedelta(days=hops.back_offset_days)


def _as_legs(found: list[Finding], hops: Hops) -> list[Finding]:
    for f in found:
        f.leg, f.is_deal, f.reasons = True, False, []
        f.origin = hops.hubs.get(f.from_code, f.from_code)
        f.key = "leg|" + f.key
    return found


def google_legs(trip: Trip, hops: Hops, out: date, back: date, api_key: str) -> list[Finding]:
    """One search: every hub to every onward airport, for the middle of the trip."""
    leg_out, leg_back = leg_dates(hops, out, back)
    hub = Origin(name="hub", airports=",".join(hops.hubs), city="")
    onward = Region(name=REGION, deal_price=0, airports=hops.onward)
    return _as_legs(google_flights.search(trip, hub, onward, leg_out, leg_back, api_key), hops)


def travelpayouts_legs(trip: Trip, hops: Hops, token: str,
                       cities: dict[str, tuple[str, str]]) -> tuple[list[Finding], list[str]]:
    """Recently seen hub -> onward fares (free). Returns legs and per-hub errors."""
    onward = {c.strip() for c in hops.onward.split(",")}
    legs, errors = [], []
    for code, name in hops.hubs.items():
        try:
            rows = travelpayouts.fetch_prices(trip, Origin(name=name, airports=code, city=code), token)
        except Exception as e:
            errors.append(f"Travelpayouts {name}: {e}")
            continue
        cheapest: dict[tuple, dict] = {}
        for row in rows:
            try:
                out = date.fromisoformat(row["departure_at"][:10])
                back = date.fromisoformat(row["return_at"][:10])
                price = float(row["price"])
            except (KeyError, TypeError, ValueError):
                continue
            dest = row.get("destination", "")
            if dest not in onward or not (trip.depart[0] < out <= back < trip.ret[1]):
                continue
            k = (dest, out, back)
            if k not in cheapest or price < cheapest[k]["_price"]:
                cheapest[k] = {**row, "_price": price, "_out": out, "_back": back}
        for (dest, out, back), row in cheapest.items():
            link = row.get("link")
            legs.append(Finding(
                key=f"leg|tp|{code}|{dest}|{out}|{back}", source=travelpayouts.SOURCE, origin=name,
                kind="fare", place=f"{cities.get(dest, (dest, ''))[0]} ({dest})", expires=out,
                price=row["_price"], depart=out, ret=back, details=f"{row.get('airline', '?')}",
                url=f"https://www.aviasales.com{link}" if link else None,
                from_code=code, dest_code=dest, leg=True))
    return legs, errors


def combine(trip: Trip, hops: Hops, findings: list[Finding]) -> list[Finding]:
    """Pair each home -> hub fare with each hub -> onward fare that fits inside it."""
    def money(p: float) -> str:
        return f"{trip.currency} {p:,.0f}"

    def span(f: Finding) -> str:
        return f"{f.depart:%b %d} to {f.ret:%b %d}"

    def brief(f: Finding) -> str:
        """Airline and stops, without the 'From XXX.' prefix (the line already says where from)."""
        return re.sub(r"^From \S+\. ", "", f.details.splitlines()[0])

    fares = [f for f in findings if f.kind == "fare" and f.price is not None and f.depart and f.ret]
    first = [f for f in fares if not f.leg and f.dest_code in hops.hubs]
    second = [f for f in fares if f.leg]
    direct: dict[tuple[str, str], Finding] = {}
    for f in fares:
        if not f.leg:
            k = (f.origin, f.dest_code)
            if k not in direct or f.price < direct[k].price:
                direct[k] = f

    best: dict[tuple[str, str], tuple[Finding, Finding]] = {}
    for a in first:
        for b in second:
            if b.from_code != a.dest_code or not (a.depart < b.depart and b.ret < a.ret):
                continue
            k = (a.origin, b.dest_code)
            if k not in best or a.price + b.price < sum(x.price for x in best[k]):
                best[k] = (a, b)

    combos = []
    for (origin, dest), (a, b) in best.items():
        hub = hops.hubs[a.dest_code]
        total = a.price + b.price
        lines = [
            f"1) {origin} to {hub}, {span(a)}: {money(a.price)} ({a.source}; {brief(a)})",
            f"2) {hub} to {b.place}, {span(b)}: {money(b.price)} ({b.source}; {brief(b)})",
        ]
        reasons = []
        if total + a.extra_cost <= hops.deal_price:
            reasons.append(f"both tickets together under {money(hops.deal_price)}")
        d = direct.get((origin, dest))
        if d:
            saving = d.price - total
            lines.append(f"Flying {origin} to {dest} directly instead: {money(d.price)}"
                         + (f" (the hop saves {money(saving)})" if saving > 0 else " (direct is cheaper)"))
            if total <= d.price * (1 - hops.min_saving_pct / 100):
                reasons.append(f"saves {saving / d.price:.0%} over flying there directly")
        lines.append("Two separate tickets: a delay on one won't be covered by the other, so keep the buffer day.")
        if b.url:
            lines.append(f"Second ticket: {b.url}")
        combos.append(Finding(
            key=f"hop|{origin}|{a.dest_code}|{dest}|{a.depart}|{a.ret}",
            source=a.source if a.source == b.source else f"{a.source} + {b.source}",
            origin=origin, kind="fare", place=f"{b.place} via {hub}", region=REGION,
            price=total, extra_cost=a.extra_cost, depart=a.depart, ret=a.ret,
            details="\n".join(lines), url=a.url, from_code=a.from_code, dest_code=dest,
            is_deal=bool(reasons), reasons=reasons, expires=a.depart))
    return sorted(combos, key=lambda f: f.price)
