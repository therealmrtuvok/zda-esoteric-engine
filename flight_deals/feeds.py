"""Deal-site posts from RSS/Atom feeds, filtered to your city, regions and dates.

Feeds are published for exactly this kind of automated reading, unlike airline
and booking sites, which forbid scraping and block it.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from common import Feed, FetchError, Finding, Region, Trip, http_get

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


XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
FEED_LINK = re.compile(
    rb"<link[^>]+type=[\"']application/(?:rss|atom)\+xml[\"'][^>]*>", re.I)


def _looks_like_html(raw: bytes) -> bool:
    head = raw[:1000].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<html" in head[:300]


def discover(page: bytes, base: str) -> str | None:
    """The feed URL a web page advertises in its <link rel="alternate"> tag."""
    for tag in FEED_LINK.findall(page):
        m = re.search(rb"href=[\"']([^\"']+)[\"']", tag)
        if m:
            return urllib.parse.urljoin(base, html.unescape(m.group(1).decode(errors="replace")))
    return None


def _root(xml: bytes) -> ET.Element:
    """Parse a feed, forgiving the two most common mistakes: bare '&' and HTML entities."""
    try:
        return ET.fromstring(xml)
    except ET.ParseError:
        fixed = re.sub(rb"&(?!#\d+;|#x[0-9a-fA-F]+;|\w+;)", b"&amp;", xml)
        fixed = re.sub(rb"&(\w+);", lambda m: m.group(0) if m.group(1).decode() in XML_ENTITIES
                       else html.unescape(m.group(0).decode()).encode("ascii", "xmlcharrefreplace"), fixed)
        return ET.fromstring(fixed)


def fetch(url: str) -> bytes:
    """Fetch a feed; given a web page instead, follow the feed link it advertises."""
    raw = http_get(url, timeout=45)
    if not _looks_like_html(raw):
        return raw
    feed_url = discover(raw, url)
    if not feed_url:
        raise FetchError("got a web page with no feed link (the site may be blocking automated requests)")
    raw = http_get(feed_url, timeout=45)
    if _looks_like_html(raw):
        raise FetchError(f"{feed_url} returned a web page, not a feed (likely bot protection)")
    return raw


def parse(xml: bytes) -> list[Item]:
    root = _root(xml)
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
    if feed.from_origin_only:
        origin = trip.origins[0]
    else:
        origin = next((o for o in trip.origins if _mentions(text, o.keywords)), None)
        if origin is None:
            return None
    region = next((r for r in regions if _mentions(text, r.keywords)), None)
    if region is None or not HOLIDAY_DATES.search(text):
        return None
    m = PRICE.search(item.title) or PRICE.search(item.text)
    price = float(m.group(1).replace(",", "")) if m else None
    if price is not None and price + origin.extra_cost > trip.max_price:
        return None
    return Finding(
        key=f"feed|{item.link or item.title}",
        source=feed.name,
        origin=origin.name,
        extra_cost=origin.extra_cost,
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
    items = parse(fetch(feed.url))
    found = [match(i, feed, trip, regions, now, max_age_days) for i in items]
    return [f for f in found if f]
