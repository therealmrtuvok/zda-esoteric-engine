"""Shared config, data model and HTTP helpers for the flight deal watcher."""
from __future__ import annotations

import json
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; flight-deals-watcher/2.0; personal use)"


# ---------------------------------------------------------------- config

@dataclass
class Origin:
    name: str                        # "Toronto", "Buffalo"
    airports: str                    # Google Flights airport code(s), e.g. "YYZ,YTZ"
    city: str                        # Travelpayouts city code, e.g. "YTO" (all Toronto airports)
    keywords: list[str] = field(default_factory=list)  # how deal sites name it
    extra_cost: float = 0            # cost of getting there and back (drive, parking), added to fares


@dataclass
class Trip:
    origins: list[Origin]
    depart: tuple[date, date]        # earliest and latest outbound date
    ret: tuple[date, date]           # earliest and latest return date
    max_price: float                 # budget: anything at or under this is worth showing
    google_trips: list[tuple[date, date]]
    currency: str = "CAD"
    adults: int = 1

    def fits(self, out: date, back: date | None) -> bool:
        if not (self.depart[0] <= out <= self.depart[1]):
            return False
        return back is None or self.ret[0] <= back <= self.ret[1]


@dataclass
class Region:
    name: str
    deal_price: float                # at or under this, it's a DEAL, not just an option
    airports: str = ""               # Google Flights destinations, comma-separated (7 max)
    countries: set[str] = field(default_factory=set)   # ISO codes, for Travelpayouts
    cities: set[str] = field(default_factory=set)      # city codes, for Travelpayouts; beat countries
    keywords: list[str] = field(default_factory=list)  # place names, for deal-site posts
    origins: list[str] = field(default_factory=list)   # Google Flights searches only from these (default: all)


@dataclass
class Feed:
    name: str
    url: str
    from_origin_only: bool = False   # every post is already from your city (e.g. YYZ Deals)


@dataclass
class Hops:
    """Fly to a hub first, then take a separate round trip from there."""
    name: str                        # e.g. "Hop via Colombia"; also its region name in alerts
    hubs: dict[str, str]             # airport code -> name, e.g. {"MDE": "Medellín"}
    onward: str                      # where to go from the hub (Google Flights codes, 7 max)
    onward_cities: list[str] = field(default_factory=list)  # Travelpayouts city codes, e.g. ["RIO"]
    tp_cities: dict[str, str] = field(default_factory=dict)  # hub airport -> Travelpayouts city, e.g. JFK -> NYC
    deal_price: float = 850          # total for both tickets at or under this is a DEAL
    min_saving_pct: float = 15       # ...or this much cheaper than flying there directly
    out_offset_days: int = 1         # second trip leaves the hub this long after you land
    back_offset_days: int = 1        # ...and is back this long before your flight home


@dataclass
class Settings:
    max_searches_per_run: int = 6    # Google Flights searches per run (SerpApi quota)
    realert_drop_pct: float = 10.0
    max_individual_alerts: int = 5   # beyond this, new finds go into the digest
    feed_max_age_days: int = 3
    daily_summary: bool = True       # quiet "nothing new" summary when nothing is found


@dataclass
class Config:
    trip: Trip
    regions: list[Region]
    feeds: list[Feed]
    settings: Settings
    hops: list[Hops] = field(default_factory=list)


def _d(s: str) -> date:
    return date.fromisoformat(s)


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    t = dict(raw["trip"])
    origins = [Origin(**o) for o in raw.get("origins", [])]
    if not origins:
        raise ValueError("config needs at least one [[origins]] block")
    trip = Trip(
        origins=origins,
        depart=(_d(t["depart"][0]), _d(t["depart"][1])),
        ret=(_d(t["return"][0]), _d(t["return"][1])),
        max_price=float(t.pop("max_price")),
        google_trips=[(_d(a), _d(b)) for a, b in t.pop("google_trips", [])],
        **{k: v for k, v in t.items() if k not in ("depart", "return")},
    )
    for out, back in trip.google_trips:
        if not trip.fits(out, back):
            raise ValueError(f"google_trips {out} to {back} is outside the trip's depart/return windows")
    regions = []
    for r in raw.get("regions", []):
        r = dict(r)
        r["countries"] = set(r.get("countries", []))
        r["cities"] = set(r.get("cities", []))
        region = Region(**r)
        if len([a for a in region.airports.split(",") if a.strip()]) > 7:
            raise ValueError(f"{region.name}: Google Flights takes at most 7 destination airports")
        regions.append(region)
    feeds = [Feed(**f) for f in raw.get("feeds", [])]
    hops = [Hops(**h) for h in raw.get("hops", [])]
    for h in hops:
        if len(h.onward.split(",")) > 7:
            raise ValueError(f"hops {h.name}: Google Flights takes at most 7 destination airports")
        if h.name in {r.name for r in regions}:
            raise ValueError(f"hops {h.name}: name clashes with a region")
    return Config(trip, regions, feeds, Settings(**raw.get("settings", {})), hops)


# ---------------------------------------------------------------- findings

@dataclass
class Finding:
    """One thing worth possibly telling you about: a fare, or a deal-site post."""
    key: str                         # stable identity, for not alerting twice
    source: str                      # "Google Flights", "Travelpayouts", or the feed's name
    origin: str                      # which origin it's from, e.g. "Buffalo"
    kind: str                        # "fare" or "post"
    place: str                       # "Lisbon (LIS)", or the post's title
    expires: date                    # forget it after this date
    region: str | None = None
    price: float | None = None
    depart: date | None = None
    ret: date | None = None
    details: str = ""                # airline and stops, or a post excerpt
    url: str | None = None
    extra_cost: float = 0            # the origin's travel cost, added to compare fairly
    from_code: str = ""              # departure airport/city code
    dest_code: str = ""              # destination airport/city code
    leg: bool = False                # one half of a hop trip: priced, but never alerted on its own
    is_deal: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def total(self) -> float | None:
        """Fare plus the cost of getting to the origin airport: what budgets and deals compare."""
        return None if self.price is None else self.price + self.extra_cost


# ---------------------------------------------------------------- http

class FetchError(RuntimeError):
    pass


def http_get(url: str, timeout: int = 60, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise FetchError(f"HTTP {e.code}: {body}") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise FetchError(str(getattr(e, "reason", e))) from None


def http_json(url: str, **kw) -> dict:
    try:
        return json.loads(http_get(url, **kw))
    except json.JSONDecodeError as e:
        raise FetchError(f"not JSON: {e}") from None
