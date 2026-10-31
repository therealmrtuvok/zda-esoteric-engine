"""Cheapest recently-seen fares from your city to anywhere, via the Travelpayouts
(Aviasales) Data API: https://support.travelpayouts.com/hc/en-us/articles/203956163

These prices come from searches other travellers made in roughly the last few
days, so they're a great way to discover cheap destinations, but they can be
stale. Always re-check the fare before booking.
"""
from __future__ import annotations

import urllib.parse
from datetime import date

from common import FetchError, Finding, Origin, Region, Trip, http_json

PRICES_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
CITIES_URL = "https://api.travelpayouts.com/data/en/cities.json"
SOURCE = "Travelpayouts"


def city_countries() -> dict[str, tuple[str, str]]:
    """City IATA code -> (city name, ISO country code). Public, no token needed."""
    cities = http_json(CITIES_URL, timeout=90)
    if not isinstance(cities, list):
        raise FetchError("unexpected cities.json format")
    return {c["code"]: (c.get("name") or c["code"], c.get("country_code") or "")
            for c in cities if c.get("code")}


def month_pairs(trip: Trip) -> list[tuple[str, str]]:
    """The (departure month, return month) combinations the trip windows touch."""
    def months(a: date, b: date) -> list[str]:
        out, d = [], a.replace(day=1)
        while d <= b:
            out.append(d.strftime("%Y-%m"))
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        return out
    return [(dm, rm) for dm in months(*trip.depart) for rm in months(*trip.ret)]


def fetch_prices(trip: Trip, origin: Origin, token: str) -> list[dict]:
    rows = []
    for dep_month, ret_month in month_pairs(trip):
        q = {"origin": origin.city, "departure_at": dep_month, "return_at": ret_month,
             "one_way": "false", "direct": "false", "sorting": "price", "unique": "false",
             "currency": trip.currency.lower(), "limit": 1000, "page": 1}
        data = http_json(PRICES_URL + "?" + urllib.parse.urlencode(q),
                         headers={"X-Access-Token": token})
        if not data.get("success", False):
            raise FetchError(f"Travelpayouts: {data.get('error') or data}")
        rows.extend(data.get("data") or [])
    return rows


def parse(trip: Trip, origin: Origin, regions: list[Region], rows: list[dict],
          cities: dict[str, tuple[str, str]]) -> list[Finding]:
    """Cheapest fitting fare per destination, limited to destinations in your regions."""
    by_country = {c: r for r in regions for c in r.countries}
    cheapest: dict[str, dict] = {}
    for row in rows:
        try:
            out = date.fromisoformat(row["departure_at"][:10])
            back = date.fromisoformat(row["return_at"][:10])
            price = float(row["price"])
        except (KeyError, TypeError, ValueError):
            continue
        dest = row.get("destination", "")
        _, country = cities.get(dest, ("", ""))
        if country not in by_country or not trip.fits(out, back):
            continue
        if dest not in cheapest or price < cheapest[dest]["_price"]:
            cheapest[dest] = {**row, "_price": price, "_out": out, "_back": back}

    findings = []
    for dest, row in cheapest.items():
        city, country = cities[dest]
        region = by_country[country]
        stops = int(row.get("transfers") or 0)
        details = (f"From {row.get('origin_airport') or origin.city}. {row.get('airline', '?')}, {'nonstop' if stops == 0 else f'{stops} stop' + 's' * (stops > 1)}"
                   " outbound. Seen in recent searches, so re-check the price.")
        link = row.get("link")
        is_deal = row["_price"] + origin.extra_cost <= region.deal_price
        findings.append(Finding(
            key=f"tp|{origin.name}|{dest}",
            source=SOURCE,
            origin=origin.name,
            extra_cost=origin.extra_cost,
            kind="fare",
            place=f"{city} ({dest})",
            region=region.name,
            price=row["_price"],
            depart=row["_out"],
            ret=row["_back"],
            details=details,
            url=f"https://www.aviasales.com{link}" if link else None,
            is_deal=is_deal,
            reasons=[f"under the {trip.currency} {region.deal_price:,.0f} deal mark for {region.name}"] if is_deal else [],
            expires=trip.depart[1],
        ))
    return sorted(findings, key=lambda f: f.price)
