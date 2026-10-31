#!/usr/bin/env python3
"""Flight deal watcher: searches Google Flights through SerpApi and pushes
deals to your phone through ntfy.

Standard library only (Python 3.11+). Configure routes in config.toml.

Environment:
  SERPAPI_KEY   SerpApi API key (required unless --dry-run)
  NTFY_TOPIC    ntfy topic to publish to (required to send alerts)
  NTFY_SERVER   ntfy server, default https://ntfy.sh
  NTFY_TOKEN    optional access token for a protected ntfy topic

Usage:
  python deals.py                 search, alert on new deals, update state
  python deals.py --dry-run       show the searches that would run, spend nothing
  python deals.py --no-notify     search and print deals, but don't push or save state
  python deals.py --test-notify   send one test push to check the ntfy setup
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERPAPI_URL = "https://serpapi.com/search.json"
STOPS = {"any": 0, "nonstop": 1, "1": 2, "2": 3}  # SerpApi `stops` values
CLASSES = {"economy": 1, "premium": 2, "business": 3, "first": 4}


# ---------------------------------------------------------------- config

@dataclass
class Route:
    name: str
    origin: str
    destination: str
    trip: str = "round"            # "round" or "oneway"
    nights: list[int] = field(default_factory=lambda: [7])
    depart_in_days: list[int] = field(default_factory=list)
    depart_dates: list[str] = field(default_factory=list)
    max_price: float | None = None
    alert_on_google_low: bool = True
    stops: str = "any"
    cabin: str = "economy"


@dataclass
class Settings:
    currency: str = "USD"
    adults: int = 1
    max_searches_per_run: int = 8
    realert_drop_pct: float = 10.0


def load_config(path: Path) -> tuple[Settings, list[Route]]:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    settings = Settings(**raw.get("settings", {}))
    routes = []
    for r in raw.get("routes", []):
        r = dict(r)
        if not r.pop("enabled", True):
            continue
        r["origin"] = r.pop("from")
        r["destination"] = r.pop("to")
        if isinstance(r.get("nights"), int):
            r["nights"] = [r["nights"]]
        route = Route(**r)
        if route.trip not in ("round", "oneway"):
            raise ValueError(f"{route.name}: trip must be 'round' or 'oneway'")
        if route.stops not in STOPS:
            raise ValueError(f"{route.name}: stops must be one of {list(STOPS)}")
        if route.cabin not in CLASSES:
            raise ValueError(f"{route.name}: cabin must be one of {list(CLASSES)}")
        if not (route.depart_in_days or route.depart_dates):
            raise ValueError(f"{route.name}: set depart_in_days or depart_dates")
        if route.max_price is None and not route.alert_on_google_low:
            raise ValueError(f"{route.name}: set max_price or alert_on_google_low")
        routes.append(route)
    return settings, routes


# ---------------------------------------------------------------- searches

@dataclass(frozen=True)
class Search:
    route: Route
    outbound: date
    inbound: date | None

    @property
    def key(self) -> str:
        back = self.inbound.isoformat() if self.inbound else "oneway"
        return f"{self.route.origin}-{self.route.destination}|{self.outbound}|{back}"


def plan_searches(routes: list[Route], today: date) -> list[Search]:
    """Expand every route into concrete (outbound, inbound) date pairs.

    Searches are interleaved across routes, so a per-run cap still covers
    every route instead of spending the whole budget on the first one.
    """
    per_route = []
    for route in routes:
        outbounds = [today + timedelta(days=d) for d in route.depart_in_days]
        outbounds += [date.fromisoformat(d) for d in route.depart_dates]
        outbounds = sorted({d for d in outbounds if d > today})
        items = []
        for out in outbounds:
            if route.trip == "oneway":
                items.append(Search(route, out, None))
            else:
                items.extend(Search(route, out, out + timedelta(days=n)) for n in route.nights)
        per_route.append(items)
    interleaved = []
    for i in range(max((len(x) for x in per_route), default=0)):
        interleaved.extend(x[i] for x in per_route if i < len(x))
    return interleaved


def serpapi_params(search: Search, settings: Settings, api_key: str) -> dict:
    r = search.route
    params = {
        "engine": "google_flights",
        "departure_id": r.origin,
        "arrival_id": r.destination,
        "outbound_date": search.outbound.isoformat(),
        "type": 1 if search.inbound else 2,
        "currency": settings.currency,
        "hl": "en",
        "adults": settings.adults,
        "travel_class": CLASSES[r.cabin],
        "stops": STOPS[r.stops],
        "api_key": api_key,
    }
    if search.inbound:
        params["return_date"] = search.inbound.isoformat()
    return params


def fetch(search: Search, settings: Settings, api_key: str) -> dict:
    url = SERPAPI_URL + "?" + urllib.parse.urlencode(serpapi_params(search, settings, api_key))
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"SerpApi HTTP {e.code}: {body}") from None
    if data.get("error"):
        raise RuntimeError(f"SerpApi: {data['error']}")
    return data


# ---------------------------------------------------------------- deals

@dataclass
class Deal:
    search: Search
    price: float
    airlines: list[str]
    stops: int
    duration_min: int | None
    price_level: str | None
    typical_range: list[float] | None
    url: str | None
    reasons: list[str]


def find_deal(search: Search, data: dict) -> Deal | None:
    """Return the cheapest itinerary if it meets the route's deal rules."""
    options = [o for o in data.get("best_flights", []) + data.get("other_flights", [])
               if isinstance(o.get("price"), (int, float))]
    if not options:
        return None
    best = min(options, key=lambda o: o["price"])
    insights = data.get("price_insights") or {}
    level = insights.get("price_level")
    route = search.route

    reasons = []
    if route.max_price is not None and best["price"] <= route.max_price:
        reasons.append(f"under your {route.max_price:g} limit")
    if route.alert_on_google_low and level == "low":
        reasons.append("Google rates this price low")
    if not reasons:
        return None

    segments = best.get("flights", [])
    airlines = list(dict.fromkeys(s.get("airline", "?") for s in segments))
    return Deal(
        search=search,
        price=best["price"],
        airlines=airlines,
        stops=max(len(segments) - 1, 0),
        duration_min=best.get("total_duration"),
        price_level=level,
        typical_range=insights.get("typical_price_range"),
        url=(data.get("search_metadata") or {}).get("google_flights_url"),
        reasons=reasons,
    )


# ---------------------------------------------------------------- state

def load_state(path: Path, today: date) -> dict:
    """Previously alerted deals, minus any whose departure date has passed."""
    try:
        state = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in state.items()
            if date.fromisoformat(k.split("|")[1]) >= today}


def is_new(deal: Deal, state: dict, realert_drop_pct: float) -> bool:
    """Alert once per route and dates, then again only if it gets clearly cheaper."""
    prev = state.get(deal.search.key)
    if prev is None:
        return True
    return deal.price <= prev["price"] * (1 - realert_drop_pct / 100)


# ---------------------------------------------------------------- notify

def format_deal(deal: Deal, currency: str) -> tuple[str, str]:
    s = deal.search
    title = f"{s.route.name}: {currency} {deal.price:,.0f}"
    dates = s.outbound.strftime("%a %d %b")
    if s.inbound:
        dates += f" to {s.inbound.strftime('%a %d %b')} ({(s.inbound - s.outbound).days} nights)"
    else:
        dates += " (one way)"
    lines = [dates]
    stops = "nonstop" if deal.stops == 0 else f"{deal.stops} stop{'s' * (deal.stops > 1)}"
    detail = f"{', '.join(deal.airlines)}, {stops}"
    if deal.duration_min:
        detail += f", {deal.duration_min // 60}h{deal.duration_min % 60:02d} outbound"
    lines.append(detail)
    if deal.typical_range and len(deal.typical_range) == 2:
        lo, hi = deal.typical_range
        lines.append(f"Typical: {currency} {lo:,.0f} to {hi:,.0f}")
    lines.append("Why: " + "; ".join(deal.reasons))
    return title, "\n".join(lines)


def ntfy_send(title: str, message: str, click: str | None = None,
              priority: str = "high", tags: str = "airplane") -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        raise RuntimeError("NTFY_TOPIC is not set")
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    # JSON publishing keeps non-ASCII titles intact (HTTP headers are latin-1 only).
    payload = {"topic": topic, "title": title, "message": message,
               "priority": {"default": 3, "high": 4, "urgent": 5}.get(priority, 3),
               "tags": tags.split(",")}
    if click:
        payload["click"] = click
        payload["actions"] = [{"action": "view", "label": "Open in Google Flights", "url": click}]
    headers = {"Content-Type": "application/json"}
    if os.environ.get("NTFY_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['NTFY_TOKEN']}"
    req = urllib.request.Request(server, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30):
        pass


# ---------------------------------------------------------------- main

def run(args) -> int:
    settings, routes = load_config(args.config)
    today = datetime.now(timezone.utc).date()
    searches = plan_searches(routes, today)
    planned = len(searches)
    searches = searches[: settings.max_searches_per_run]

    print(f"{len(routes)} route(s), {planned} search(es) planned, "
          f"running {len(searches)} (max_searches_per_run={settings.max_searches_per_run})")
    if args.dry_run:
        for s in searches:
            print(f"  {s.route.name}: {s.key}")
        return 0

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("SERPAPI_KEY is not set", file=sys.stderr)
        return 2

    notify = not args.no_notify
    state = load_state(args.state, today)
    errors, sent = [], 0
    for s in searches:
        try:
            data = fetch(s, settings, api_key)
        except Exception as e:  # keep going: one bad route shouldn't sink the run
            errors.append(f"{s.route.name} {s.key}: {e}")
            print(f"  ERROR {errors[-1]}", file=sys.stderr)
            continue
        deal = find_deal(s, data)
        if deal is None:
            print(f"  {s.key}: no deal")
            continue
        if not is_new(deal, state, settings.realert_drop_pct):
            print(f"  {s.key}: {deal.price:g} already alerted")
            continue
        title, body = format_deal(deal, settings.currency)
        print(f"  DEAL {title}\n    " + body.replace("\n", "\n    "))
        if notify:
            ntfy_send(title, body, click=deal.url)
            state[s.key] = {"price": deal.price,
                            "alerted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            sent += 1

    if notify:
        args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(f"{sent} alert(s) sent, {len(errors)} error(s)")

    if errors and len(errors) == len(searches):
        # Every search failed (bad key, quota used up...). Say so rather than going quiet.
        if notify:
            try:
                ntfy_send("Flight deals: every search failed", "\n".join(errors)[:1000],
                          priority="default", tags="warning")
            except Exception as e:
                print(f"  could not send failure alert: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--config", type=Path, default=HERE / "config.toml")
    p.add_argument("--state", type=Path, default=HERE / "state.json")
    p.add_argument("--dry-run", action="store_true", help="list searches without calling the API")
    p.add_argument("--no-notify", action="store_true", help="don't push alerts or save state")
    p.add_argument("--test-notify", action="store_true", help="send one test push and exit")
    args = p.parse_args(argv)
    if args.test_notify:
        ntfy_send("Flight deals: test", "If you can read this, alerts will reach you.",
                  priority="default", tags="white_check_mark")
        print("Test notification sent")
        return 0
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
