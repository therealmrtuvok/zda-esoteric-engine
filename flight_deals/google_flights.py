"""Live Google Flights prices through SerpApi (https://serpapi.com/google-flights-api).

One search covers a whole region: Google Flights accepts up to 7 destination
airports at once and returns the cheapest across them. Each origin is searched
separately so fares from, say, Toronto and Buffalo can be compared.
"""
from __future__ import annotations

import urllib.parse
from datetime import date

from common import FetchError, Finding, Origin, Region, Trip, http_json

SERPAPI_URL = "https://serpapi.com/search.json"
SOURCE = "Google Flights"


Search = tuple[Origin, Region, date, date]


def plan(trip: Trip, regions: list[Region], today: date) -> list[Search]:
    """Today's searches: one date pair (rotating daily through google_trips), for
    every origin and region. Rotating keeps the daily search count flat however
    many date pairs there are, and still covers each of them every few days.
    """
    if not trip.google_trips:
        return []
    out, back = trip.google_trips[today.toordinal() % len(trip.google_trips)]
    return [(o, r, out, back) for o in trip.origins for r in regions
            if r.airports and (not r.origins or o.name in r.origins)]


def params(trip: Trip, origin: Origin, region: Region, out: date, back: date, api_key: str) -> dict:
    return {
        "engine": "google_flights",
        "departure_id": origin.airports.replace(" ", ""),
        "arrival_id": region.airports.replace(" ", ""),
        "outbound_date": out.isoformat(),
        "return_date": back.isoformat(),
        "type": 1,                      # round trip
        "currency": trip.currency,
        "hl": "en",
        "gl": "ca",
        "adults": trip.adults,
        "travel_class": 1,              # economy
        "api_key": api_key,
    }


def search(trip: Trip, origin: Origin, region: Region, out: date, back: date,
           api_key: str) -> list[Finding]:
    url = SERPAPI_URL + "?" + urllib.parse.urlencode(params(trip, origin, region, out, back, api_key))
    data = http_json(url, timeout=90)
    if data.get("error"):
        # SerpApi reports "no results" as an error too; that isn't a failure.
        if "hasn't returned any results" in data["error"]:
            return []
        raise FetchError(f"SerpApi: {data['error']}")
    return parse(trip, origin, region, out, back, data)


def parse(trip: Trip, origin: Origin, region: Region, out: date, back: date,
          data: dict) -> list[Finding]:
    """The cheapest itinerary to EACH destination airport in a SerpApi response.

    A region search covers several airports at once; reporting only the overall
    cheapest would hide every other destination's price.
    """
    options = [o for o in data.get("best_flights", []) + data.get("other_flights", [])
               if isinstance(o.get("price"), (int, float)) and o.get("flights")]
    cheapest: dict[str, dict] = {}
    for o in options:
        dest = o["flights"][-1].get("arrival_airport", {}).get("id", "?")
        if dest not in cheapest or o["price"] < cheapest[dest]["price"]:
            cheapest[dest] = o
    if not cheapest:
        return []

    insights = data.get("price_insights") or {}
    overall = min(cheapest.values(), key=lambda o: o["price"])
    url = (data.get("search_metadata") or {}).get("google_flights_url")
    findings = []
    for dest, best in cheapest.items():
        legs = best["flights"]
        departure = legs[0].get("departure_airport", {}).get("id")
        arrival = legs[-1].get("arrival_airport", {})
        place = f"{arrival.get('name', '?')} ({dest})"
        airlines = ", ".join(dict.fromkeys(leg.get("airline", "?") for leg in legs))
        stops = len(legs) - 1
        details = f"{airlines}, {'nonstop' if stops == 0 else f'{stops} stop' + 's' * (stops > 1)}"
        if departure:
            details = f"From {departure}. " + details
        if best.get("total_duration"):
            details += f", {best['total_duration'] // 60}h{best['total_duration'] % 60:02d} each way approx."

        reasons = []
        if best["price"] + origin.extra_cost <= region.deal_price:
            reasons.append(f"under the {trip.currency} {region.deal_price:,.0f} deal mark for {region.name}")
        # Google's price rating and typical range describe the search as a whole,
        # i.e. its cheapest result, so only attach them to that one.
        if best is overall:
            if insights.get("price_level") == "low":
                reasons.append("Google rates this price low")
            typical = insights.get("typical_price_range")
            if typical and len(typical) == 2:
                details += f"\nTypical for this search: {trip.currency} {typical[0]:,.0f} to {typical[1]:,.0f}"

        findings.append(Finding(
            key=f"gf|{origin.name}|{dest}|{out}|{back}",
            source=SOURCE,
            origin=origin.name,
            extra_cost=origin.extra_cost,
            kind="fare",
            place=place,
            region=region.name,
            price=float(best["price"]),
            depart=out,
            ret=back,
            details=details,
            url=url,
            is_deal=bool(reasons),
            reasons=reasons,
            expires=out,
        ))
    return sorted(findings, key=lambda f: f.price)
