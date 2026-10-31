#!/usr/bin/env python3
"""Flight deal watcher: checks Google Flights (SerpApi), Travelpayouts and
deal-site feeds for your trip, and pushes what's new to your phone via ntfy.

Standard library only (Python 3.11+). Configure everything in config.toml.

Environment (each source runs only if its key is set; feeds need none):
  SERPAPI_KEY          Google Flights via SerpApi
  TRAVELPAYOUTS_TOKEN  Travelpayouts / Aviasales data API
  NTFY_TOPIC           ntfy topic to push to (without it, alerts are printed only)
  NTFY_SERVER          default https://ntfy.sh
  NTFY_TOKEN           optional, for a protected topic

Usage:
  python deals.py                 check everything, push new finds, remember them
  python deals.py --dry-run       show what would be checked, call nothing
  python deals.py --no-notify     check and print, but don't push or save state
  python deals.py --test-notify   send one test push
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import feeds as feeds_src  # noqa: E402
import google_flights  # noqa: E402
import travelpayouts  # noqa: E402
from common import Config, Finding, load_config  # noqa: E402

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------- state

def load_state(path: Path, today: date) -> dict:
    """What was already pushed, minus anything that has expired."""
    try:
        state = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    keep = {}
    for k, v in state.items():
        try:
            if date.fromisoformat(v["expires"]) >= today:
                keep[k] = v
        except (KeyError, TypeError, ValueError):
            pass
    return keep


def is_new(f: Finding, state: dict, realert_drop_pct: float) -> bool:
    """New, or (for fares) clearly cheaper than when it was last pushed."""
    prev = state.get(f.key)
    if prev is None:
        return True
    if f.price is None or prev.get("price") is None:
        return False
    return f.price <= prev["price"] * (1 - realert_drop_pct / 100)


def remember(f: Finding, state: dict) -> None:
    state[f.key] = {"price": f.price, "expires": f.expires.isoformat(),
                    "pushed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


# ---------------------------------------------------------------- formatting

def money(cfg: Config, price: float | None) -> str:
    return f"{cfg.trip.currency} {price:,.0f}" if price is not None else ""


def priced(f: Finding, cfg: Config) -> str:
    """'CAD 520', or for an origin with a travel cost, 'CAD 520 (+150 to get to Buffalo)'."""
    if f.price is None:
        return ""
    s = money(cfg, f.price)
    if f.extra_cost:
        s += f" (+{f.extra_cost:,.0f} to get to {f.origin})"
    return s


def dates(f: Finding) -> str:
    if not f.depart:
        return ""
    s = f.depart.strftime("%a %b %d")
    if f.ret:
        s += f" to {f.ret.strftime('%a %b %d')}"
    return s


def format_single(f: Finding, cfg: Config) -> dict:
    if f.kind == "post":
        title = f"Sale post: {f.place}"
        body = (f"{f.details}\n\nFrom {f.source}. It mentions {f.origin}, {f.region} and the holidays; "
                f"check that the sale covers your dates before booking.")
        return {"title": title[:250], "message": body, "click": f.url, "priority": 4, "tags": ["loudspeaker"]}
    title = f"{'DEAL: ' if f.is_deal else ''}{f.origin} to {f.place} {money(cfg, f.price)}"
    lines = [f"{dates(f)} round trip, {priced(f, cfg)}", f.details]
    if f.reasons:
        lines.append("Why: " + "; ".join(f.reasons))
    lines.append(f"Source: {f.source}")
    return {"title": title, "message": "\n".join(lines), "click": f.url,
            "priority": 5 if f.is_deal else 4, "tags": ["airplane", "rotating_light"] if f.is_deal else ["airplane"]}


def digest_line(f: Finding, cfg: Config) -> str:
    if f.kind == "post":
        return f"• {f.place} ({f.source})"
    return f"• {priced(f, cfg)}  {f.origin} to {f.place}, {dates(f)} ({f.source})"


def format_digest(items: list[Finding], cfg: Config) -> dict:
    items = sorted(items, key=lambda f: (f.total is None, f.total or 0))
    shown = items[:12]
    body = "\n".join(digest_line(f, cfg) for f in shown)
    if len(items) > len(shown):
        body += f"\n…and {len(items) - len(shown)} more"
    actions = [{"action": "view", "label": f"#{i + 1}: {f.place[:20]}", "url": f.url}
               for i, f in enumerate(shown[:3]) if f.url]
    return {"title": f"{len(items)} new option{'s' * (len(items) != 1)} under {money(cfg, cfg.trip.max_price)}",
            "message": body, "priority": 3, "tags": ["airplane"], "actions": actions}


def format_summary(findings: list[Finding], cfg: Config, checked: list[str]) -> dict:
    lines = []
    for region in cfg.regions:
        lines.append(f"{region.name}:")
        for origin in cfg.trip.origins:
            fares = [f for f in findings if f.kind == "fare" and f.region == region.name
                     and f.origin == origin.name and f.price is not None]
            if fares:
                best = min(fares, key=lambda f: f.total)
                lines.append(f"  from {origin.name}: {priced(best, cfg)}, {best.place}, {dates(best)}")
            else:
                lines.append(f"  from {origin.name}: no fares found")
    lines.append("Checked: " + ", ".join(checked))
    return {"title": "No new flight deals today", "message": "\n".join(lines),
            "priority": 2, "tags": ["calendar"]}


# ---------------------------------------------------------------- notify

def ntfy_send(msg: dict) -> None:
    topic = os.environ["NTFY_TOPIC"]
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    payload = {"topic": topic, **{k: v for k, v in msg.items() if v}}
    if msg.get("click") and "actions" not in msg:
        payload["actions"] = [{"action": "view", "label": "Open", "url": msg["click"]}]
    payload["message"] = payload.get("message", "")[:3900]
    headers = {"Content-Type": "application/json"}
    if os.environ.get("NTFY_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['NTFY_TOKEN']}"
    req = urllib.request.Request(server, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30):
        pass


# ---------------------------------------------------------------- run

def collect(cfg: Config, now: datetime, log=print) -> tuple[list[Finding], list[str], list[str], int]:
    """Run every configured source. Returns findings, errors, sources checked, sources attempted."""
    findings, errors, checked, attempted = [], [], [], 0

    key = os.environ.get("SERPAPI_KEY")
    if key:
        attempted += 1
        searches = google_flights.plan(cfg.trip, cfg.regions, now.date())[: cfg.settings.max_searches_per_run]
        ok = 0
        for origin, region, out, back in searches:
            try:
                found = google_flights.search(cfg.trip, origin, region, out, back, key)
                ok += 1
            except Exception as e:  # one bad search shouldn't sink the run
                errors.append(f"Google Flights {origin.name} to {region.name} {out}: {e}")
                continue
            log(f"  Google Flights {origin.name} to {region.name} {out}->{back}: "
                + (", ".join(f"{f.place.rsplit('(', 1)[-1].rstrip(')')} {f.price:,.0f}" for f in found)
                   or "no results"))
            findings.extend(found)
        if ok:
            checked.append(f"Google Flights ({ok} searches)")
    else:
        log("  Google Flights: skipped (no SERPAPI_KEY)")

    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if token:
        attempted += 1
        try:
            cities = travelpayouts.city_countries()
            tp_ok = 0
            for origin in cfg.trip.origins:
                try:
                    rows = travelpayouts.fetch_prices(cfg.trip, origin, token)
                except Exception as e:
                    errors.append(f"Travelpayouts {origin.name}: {e}")
                    continue
                tp_ok += 1
                found = travelpayouts.parse(cfg.trip, origin, cfg.regions, rows, cities)
                log(f"  Travelpayouts {origin.name}: {len(rows)} fares seen, "
                    f"{len(found)} destinations fit your dates and regions")
                findings.extend(found)
            if tp_ok:
                checked.append("Travelpayouts")
        except Exception as e:
            errors.append(f"Travelpayouts: {e}")
    else:
        log("  Travelpayouts: skipped (no TRAVELPAYOUTS_TOKEN)")

    feed_ok = 0
    for feed in cfg.feeds:
        try:
            found = feeds_src.scan(feed, cfg.trip, cfg.regions, now, cfg.settings.feed_max_age_days)
            feed_ok += 1
            log(f"  Feed {feed.name}: {len(found)} matching post(s)")
            findings.extend(found)
        except Exception as e:
            errors.append(f"Feed {feed.name}: {e}")
    if cfg.feeds:
        attempted += 1
        if feed_ok:
            checked.append(f"{feed_ok} deal site{'s' * (feed_ok != 1)}")

    # The same post can show up on several sites (or twice in one feed); keep the first.
    unique = list({f.key: f for f in reversed(findings)}.values())[::-1]
    return unique, errors, checked, attempted


def run(args) -> int:
    cfg = load_config(args.config)
    now = datetime.now(timezone.utc)
    today = now.date()
    if today > cfg.trip.depart[1]:
        print(f"Trip window has passed ({cfg.trip.depart[1]}). Update [trip] in config.toml for the next trip.")
        return 0

    if args.dry_run:
        print("Google Flights searches today" + ("" if os.environ.get("SERPAPI_KEY") else " (SERPAPI_KEY not set)") + ":")
        for origin, region, out, back in google_flights.plan(cfg.trip, cfg.regions, today)[: cfg.settings.max_searches_per_run]:
            print(f"  {origin.airports} -> {region.airports}  {out} to {back}  ({origin.name} to {region.name})")
        print("Travelpayouts: " + ("on" if os.environ.get("TRAVELPAYOUTS_TOKEN") else "off (TRAVELPAYOUTS_TOKEN not set)"))
        print("Feeds: " + ", ".join(f.name for f in cfg.feeds))
        return 0

    findings, errors, checked, attempted = collect(cfg, now)
    for e in errors:
        print(f"  ERROR {e}", file=sys.stderr)

    push = not args.no_notify and bool(os.environ.get("NTFY_TOPIC"))
    if not args.no_notify and not push:
        print("  (NTFY_TOPIC not set: printing alerts instead of pushing)")
    send = ntfy_send if push else (lambda m: print(f"\n[{m['title']}]\n{m['message']}\n{m.get('click') or ''}"))

    state = load_state(args.state, today)
    budget = cfg.trip.max_price
    new = [f for f in findings
           if (f.total is None or f.total <= budget) and is_new(f, state, cfg.settings.realert_drop_pct)]
    singles = [f for f in new if f.is_deal or f.kind == "post"]
    singles.sort(key=lambda f: (not f.is_deal, f.total or 0))
    singles, overflow = singles[: cfg.settings.max_individual_alerts], singles[cfg.settings.max_individual_alerts:]
    digest = [f for f in new if not (f.is_deal or f.kind == "post")] + overflow

    for f in singles:
        send(format_single(f, cfg))
    if digest:
        send(format_digest(digest, cfg))
    if not new and cfg.settings.daily_summary and checked:
        send(format_summary(findings, cfg, checked))
    for f in new:
        remember(f, state)
    if push:
        args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")

    print(f"{len(findings)} found, {len(new)} new ({len(singles)} individual, {len(digest)} in digest), "
          f"{len(errors)} error(s)")

    if attempted and not checked:
        # Every source failed (bad key, quota used up, site down). Say so rather than going quiet.
        msg = {"title": "Flight deals: every source failed", "message": "\n".join(errors)[:1500],
               "priority": 3, "tags": ["warning"]}
        try:
            send(msg)
        except Exception as e:
            print(f"  could not send failure alert: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--config", type=Path, default=HERE / "config.toml")
    p.add_argument("--state", type=Path, default=HERE / "state.json")
    p.add_argument("--dry-run", action="store_true", help="show what would be checked, call nothing")
    p.add_argument("--no-notify", action="store_true", help="print instead of pushing; don't save state")
    p.add_argument("--test-notify", action="store_true", help="send one test push and exit")
    args = p.parse_args(argv)
    if args.test_notify:
        ntfy_send({"title": "Flight deals: test", "message": "If you can read this, alerts will reach you.",
                   "priority": 3, "tags": ["white_check_mark"]})
        print("Test notification sent")
        return 0
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
