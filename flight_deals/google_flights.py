"""Live Google Flights prices through SerpApi (https://serpapi.com/google-flights-api).

One search covers a whole region: Google Flights accepts up to 7 destination
airports at once and returns the cheapest across them.
"""
from __future__ import annotations

import urllib.parse
from datetime import date

from common import FetchError, Finding, Region, Trip, http_json

SERPAPI_URL = "https://serpapi.com/search.json"
SOURCE = "Google Flights"


def plan(trip: Trip, regions: list[Region]) -> list[tuple[Region, date, date]]:
    """Every (region, outbound, return) search, ordered so a cap still covers every region."""
    return [(r, out, back) for out, back in trip.google_trips for r in regions if r.airports]


def params(trip: Trip, region: Region, out: date, back: date, api_key: str) -> dict:
    return {
        "engine": "google_flights",
        "departure_id": trip.origin,
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


def search(trip: Trip, region: Region, out: date, back: date, api_key: str) -> Finding | None:
    url = SERPAPI_URL + "?" + urllib.parse.urlencode(params(trip, region, out, back, api_key))
    data = http_json(url, timeout=90)
    if data.get("error"):
        # SerpApi reports "no results" as an error too; that isn't a failure.
        if "hasn't returned any results" in data["error"]:
            return None
        raise FetchError(f"SerpApi: {data['error']}")
    return parse(trip, region, out, back, data)


def parse(trip: Trip, region: Region, out: date, back: date, data: dict) -> Finding | None:
    """The cheapest itinerary in a SerpApi response, as a Finding."""
    options = [o for o in data.get("best_flights", []) + data.get("other_flights", [])
               if isinstance(o.get("price"), (int, float)) and o.get("flights")]
    if not options:
        return None
    best = min(options, key=lambda o: o["price"])
    legs = best["flights"]
    arrival = legs[-1].get("arrival_airport", {})
    place = f"{arrival.get('name', '?')} ({arrival.get('id', '?')})"
    airlines = ", ".join(dict.fromkeys(leg.get("airline", "?") for leg in legs))
    stops = len(legs) - 1
    details = f"{airlines}, {'nonstop' if stops == 0 else f'{stops} stop' + 's' * (stops > 1)}"
    if best.get("total_duration"):
        details += f", {best['total_duration'] // 60}h{best['total_duration'] % 60:02d} each way approx."

    insights = data.get("price_insights") or {}
    reasons = []
    if best["price"] <= region.deal_price:
        reasons.append(f"under the {trip.currency} {region.deal_price:,.0f} deal mark for {region.name}")
    if insights.get("price_level") == "low":
        reasons.append("Google rates this price low")
    typical = insights.get("typical_price_range")
    if typical and len(typical) == 2:
        details += f"\nTypical for this search: {trip.currency} {typical[0]:,.0f} to {typical[1]:,.0f}"

    return Finding(
        key=f"gf|{region.name}|{out}|{back}",
        source=SOURCE,
        kind="fare",
        place=place,
        region=region.name,
        price=float(best["price"]),
        depart=out,
        ret=back,
        details=details,
        url=(data.get("search_metadata") or {}).get("google_flights_url"),
        is_deal=bool(reasons),
        reasons=reasons,
        expires=out,
    )
