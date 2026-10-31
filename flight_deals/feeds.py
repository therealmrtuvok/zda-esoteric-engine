"""Deal-site posts from RSS/Atom feeds, filtered to your city, regions and dates.

Feeds are published for exactly this kind of automated reading, unlike airline
and booking sites, which forbid scraping and block it.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from common import Feed, Finding, Region, Trip, http_get

ATOM = "{http://www.w3.org/2005/Atom}"
HOLIDAY_DATES = re.compile(r"\b(dec(ember)?|jan(uary)?|christmas|new\s+year'?s?|holidays?)\b", re.I)
PRICE = re.compile(r"(?:C\$|CA\$|CAD\s?\$?|\$)\s?(\d{1,3}(?:,\d{3})+|\d{2,5})(?![\d,])")


@dataclass
class Item:
    title: str
    link: str
    text: str
    published: datetime | None


def _clean(s: str | None) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _when(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def parse(xml: bytes) -> list[Item]:
    root = ET.fromstring(xml)
    items = []
    for it in root.iter("item"):                       # RSS 2.0
        items.append(Item(
            title=_clean(it.findtext("title")),
            link=(it.findtext("link") or "").strip(),
            text=_clean(it.findtext("description")),
            published=_when(it.findtext("pubDate")),
        ))
    for e in root.iter(f"{ATOM}entry"):                # Atom
        link = e.find(f"{ATOM}link")
        items.append(Item(
            title=_clean(e.findtext(f"{ATOM}title")),
            link=link.get("href", "") if link is not None else "",
            text=_clean(e.findtext(f"{ATOM}summary") or e.findtext(f"{ATOM}content")),
            published=_when(e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated")),
        ))
    return items


def _mentions(text: str, words: list[str]) -> str | None:
    for w in words:
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", text, re.I):
            return w
    return None


def match(item: Item, feed: Feed, trip: Trip, regions: list[Region],
          now: datetime, max_age_days: int) -> Finding | None:
    if item.published and item.published < now - timedelta(days=max_age_days):
        return None
    text = f"{item.title} {item.text}"
    if not feed.from_origin_only and not _mentions(text, trip.origin_keywords):
        return None
    region = next((r for r in regions if _mentions(text, r.keywords)), None)
    if region is None or not HOLIDAY_DATES.search(text):
        return None
    m = PRICE.search(item.title) or PRICE.search(item.text)
    price = float(m.group(1).replace(",", "")) if m else None
    if price is not None and price > trip.max_price:
        return None
    return Finding(
        key=f"feed|{item.link or item.title}",
        source=feed.name,
        kind="post",
        place=item.title[:120],
        region=region.name,
        price=price,
        details=item.text[:280],
        url=item.link or None,
        expires=now.date() + timedelta(days=30),
    )


def scan(feed: Feed, trip: Trip, regions: list[Region], now: datetime,
         max_age_days: int) -> list[Finding]:
    items = parse(http_get(feed.url, timeout=45))
    found = [match(i, feed, trip, regions, now, max_age_days) for i in items]
    return [f for f in found if f]
