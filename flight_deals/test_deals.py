"""Tests for the flight deal watcher. Run: python -m unittest flight_deals/test_deals.py"""
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deals  # noqa: E402
import feeds  # noqa: E402
import google_flights  # noqa: E402
import travelpayouts  # noqa: E402
from common import Feed, Finding, load_config  # noqa: E402

CFG = load_config(HERE / "config.toml")
TRIP = CFG.trip
CARIB, LATAM, EUROPE = CFG.regions
NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
OUT, BACK = date(2026, 12, 27), date(2027, 1, 3)


def gf_response(prices, level=None, dest=("CUN", "Cancún International Airport")):
    def option(p):
        return {"price": p, "total_duration": 245,
                "flights": [{"airline": "WestJet", "arrival_airport": {"id": "YUL", "name": "Montréal"}},
                            {"airline": "WestJet", "arrival_airport": {"id": dest[0], "name": dest[1]}}]}
    data = {"best_flights": [option(p) for p in prices[:1]],
            "other_flights": [option(p) for p in prices[1:]],
            "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights?x"}}
    if level:
        data["price_insights"] = {"price_level": level, "typical_price_range": [800, 1100]}
    return data


RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Toronto to Cancun $489 roundtrip, December and January dates</title>
<link>https://deals.example/cancun</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate>
<description>&lt;p&gt;Nonstop on WestJet. Dates over Christmas and New Year's.&lt;/p&gt;</description></item>
<item><title>Toronto to Vancouver $199 in December</title>
<link>https://deals.example/yvr</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate></item>
<item><title>Toronto to Lisbon $520 in March</title>
<link>https://deals.example/lis</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate></item>
<item><title>Montreal to Paris $500 December</title>
<link>https://deals.example/yul</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate></item>
<item><title>Toronto to Rome $2,100 business class over New Year</title>
<link>https://deals.example/rome</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate></item>
<item><title>Toronto to Bogota $600 January</title>
<link>https://deals.example/old</link><pubDate>Mon, 19 Oct 2026 09:00:00 +0000</pubDate></item>
</channel></rss>"""

# What every feed returns in the end-to-end tests: YYZ Deals trusts all its posts
# to be from Toronto, so leave out the Montreal post it would never carry.
E2E_RSS = RSS.replace(b"""<item><title>Montreal to Paris $500 December</title>
<link>https://deals.example/yul</link><pubDate>Sun, 01 Nov 2026 09:00:00 +0000</pubDate></item>
""", b"")
assert E2E_RSS != RSS

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>YYZ - Lima, Peru $640 roundtrip | Dec-Jan</title>
<link href="https://deals.example/lima"/><updated>2026-10-31T20:00:00Z</updated>
<summary>Toronto to Lima over the holidays.</summary></entry></feed>"""


class Config(unittest.TestCase):
    def test_shipped_config(self):
        self.assertEqual([r.name for r in CFG.regions],
                         ["Caribbean & Mexico", "Central & South America", "Europe"])
        self.assertEqual(TRIP.max_price, 1500)
        self.assertTrue(all(TRIP.fits(a, b) for a, b in TRIP.google_trips))

    def test_trip_window(self):
        self.assertTrue(TRIP.fits(date(2026, 12, 30), date(2027, 1, 2)))
        self.assertFalse(TRIP.fits(date(2026, 12, 26), date(2027, 1, 2)))
        self.assertFalse(TRIP.fits(date(2026, 12, 28), date(2027, 1, 5)))


class GoogleFlights(unittest.TestCase):
    def test_plan_covers_every_region_first(self):
        plan = google_flights.plan(TRIP, CFG.regions)
        self.assertEqual(len(plan), 6)
        self.assertEqual([p[0].name for p in plan[:3]], [r.name for r in CFG.regions])

    def test_cheapest_option_and_destination(self):
        f = google_flights.parse(TRIP, CARIB, OUT, BACK, gf_response([980, 640, 720]))
        self.assertEqual(f.price, 640)
        self.assertEqual(f.place, "Cancún International Airport (CUN)")
        self.assertIn("WestJet, 1 stop", f.details)
        self.assertTrue(f.is_deal)

    def test_option_under_budget_but_not_a_deal(self):
        f = google_flights.parse(TRIP, CARIB, OUT, BACK, gf_response([1200], level="typical"))
        self.assertFalse(f.is_deal)

    def test_google_low_makes_it_a_deal(self):
        f = google_flights.parse(TRIP, EUROPE, OUT, BACK, gf_response([1200], level="low"))
        self.assertEqual(f.reasons, ["Google rates this price low"])

    def test_no_results(self):
        self.assertIsNone(google_flights.parse(TRIP, CARIB, OUT, BACK, {"best_flights": []}))
        with mock.patch.object(google_flights, "http_json",
                               return_value={"error": "Google Flights hasn't returned any results for this query."}):
            self.assertIsNone(google_flights.search(TRIP, CARIB, OUT, BACK, "k"))


class Travelpayouts(unittest.TestCase):
    CITIES = {"CUN": ("Cancun", "MX"), "LIS": ("Lisbon", "PT"), "YVR": ("Vancouver", "CA"),
              "LIM": ("Lima", "PE")}

    def row(self, dest, price, out="2026-12-28", back="2027-01-03"):
        return {"destination": dest, "price": price, "airline": "WS", "transfers": 0,
                "departure_at": f"{out}T07:00:00-05:00", "return_at": f"{back}T15:00:00-05:00",
                "link": f"/search/YTO{dest}"}

    def test_filters_dates_regions_and_keeps_cheapest(self):
        rows = [self.row("CUN", 900), self.row("CUN", 650),
                self.row("LIS", 400, out="2026-12-20"),       # leaves too early
                self.row("YVR", 300),                         # Canada: not a region
                self.row("LIM", 1100, back="2027-01-04")]
        found = travelpayouts.parse(TRIP, CFG.regions, rows, self.CITIES)
        self.assertEqual([(f.place, f.price, f.is_deal) for f in found],
                         [("Cancun (CUN)", 650, True), ("Lima (LIM)", 1100, False)])
        self.assertEqual(found[0].url, "https://www.aviasales.com/search/YTOCUN")

    def test_month_pairs(self):
        self.assertEqual(travelpayouts.month_pairs(TRIP), [("2026-12", "2027-01")])


class Feeds(unittest.TestCase):
    def scan(self, xml, feed=Feed("Test", "x")):
        with mock.patch.object(feeds, "http_get", return_value=xml):
            return feeds.scan(feed, TRIP, CFG.regions, NOW, 3)

    def test_price_with_thousands_separator(self):
        self.assertEqual(feeds.PRICE.search("from $2,100 return").group(1), "2,100")
        self.assertEqual(feeds.PRICE.search("CA$489 roundtrip").group(1), "489")

    def test_malformed_feed_is_forgiven(self):
        xml = RSS.replace(b"Toronto to Cancun $489", b"Toronto to Cancun &nbsp;$489 Sun & Sand")
        found = self.scan(xml)
        self.assertEqual(found[0].price, 489)
        self.assertIn("Sun & Sand", found[0].place)

    def test_home_page_feed_discovery(self):
        page = (b'<!DOCTYPE html><html><head><link rel="alternate" type="application/rss+xml" '
                b'href="/deals/feed.xml"></head><body>hi</body></html>')
        with mock.patch.object(feeds, "http_get", side_effect=[page, RSS]) as get:
            self.assertEqual(feeds.fetch("https://deals.example/"), RSS)
        self.assertEqual(get.call_args.args[0], "https://deals.example/deals/feed.xml")

    def test_bot_wall_reported_clearly(self):
        wall = b"<!DOCTYPE html><html><head><title>Just a moment...</title></head></html>"
        with mock.patch.object(feeds, "http_get", return_value=wall):
            with self.assertRaisesRegex(Exception, "no feed link"):
                feeds.fetch("https://deals.example/feed/")

    def test_rss_filtering(self):
        found = self.scan(RSS)
        # Vancouver: no region. Lisbon: March. Montreal: not Toronto. Rome: over budget. Bogota: too old.
        self.assertEqual([(f.place[:20], f.price, f.region) for f in found],
                         [("Toronto to Cancun $4", 489, "Caribbean & Mexico")])
        self.assertIn("Christmas", found[0].details)
        self.assertNotIn("<p>", found[0].details)

    def test_atom(self):
        found = self.scan(ATOM)
        self.assertEqual([(f.price, f.region, f.url) for f in found],
                         [(640, "Central & South America", "https://deals.example/lima")])

    def test_origin_only_feed_skips_city_check(self):
        xml = RSS.replace(b"Toronto to Cancun", b"Cancun")
        self.assertEqual(len(self.scan(xml)), 0)
        self.assertEqual(len(self.scan(xml, Feed("YYZ", "x", from_origin_only=True))), 2)  # + Montreal-Paris post


class State(unittest.TestCase):
    def finding(self, price, key="gf|x"):
        return Finding(key=key, source="s", kind="fare", place="p", expires=date(2026, 12, 27), price=price)

    def test_realert_only_on_meaningful_drop(self):
        state = {"gf|x": {"price": 1000, "expires": "2026-12-27"}}
        self.assertFalse(deals.is_new(self.finding(950), state, 10))
        self.assertTrue(deals.is_new(self.finding(900), state, 10))
        self.assertTrue(deals.is_new(self.finding(900, key="other"), state, 10))

    def test_expired_entries_pruned(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            p.write_text(json.dumps({"a": {"expires": "2026-10-01"}, "b": {"expires": "2026-12-27"},
                                     "old-format": {"price": 1}}))
            self.assertEqual(list(deals.load_state(p, date(2026, 11, 1))), ["b"])


class EndToEnd(unittest.TestCase):
    def run_main(self, d, env, gf=None, tp_rows=None, rss=E2E_RSS, tp_error=None):
        argv = ["--state", str(Path(d) / "state.json")]
        cities = Travelpayouts.CITIES
        with mock.patch.dict("os.environ", env, clear=True), \
             mock.patch.object(deals, "datetime", wraps=datetime) as dt, \
             mock.patch.object(google_flights, "http_json", side_effect=gf or (lambda *a, **k: gf_response([1250]))), \
             mock.patch.object(travelpayouts, "city_countries", return_value=cities), \
             mock.patch.object(travelpayouts, "fetch_prices", return_value=tp_rows or [], side_effect=tp_error), \
             mock.patch.object(feeds, "http_get", return_value=rss), \
             mock.patch.object(deals, "ntfy_send") as send:
            dt.now.return_value = NOW
            code = deals.main(argv)
        return code, [c.args[0] for c in send.call_args_list]

    ENV = {"SERPAPI_KEY": "k", "TRAVELPAYOUTS_TOKEN": "t", "NTFY_TOPIC": "topic"}

    def test_deals_singly_options_in_digest_then_quiet(self):
        tp = [Travelpayouts().row("CUN", 610), Travelpayouts().row("LIS", 1300)]
        with tempfile.TemporaryDirectory() as d:
            code, sent = self.run_main(d, self.ENV, tp_rows=tp)
            self.assertEqual(code, 0)
            titles = [m["title"] for m in sent]
            # Cancun fare deal and the Cancun sale post get their own pushes...
            self.assertEqual(titles[0], "DEAL: Cancun (CUN) CAD 610")
            self.assertTrue(titles[1].startswith("Sale post: Toronto to Cancun $489"))
            # ...and the six Google Flights options at 1,250 plus Lisbon at 1,300 go in one digest.
            self.assertEqual(titles[2], "7 new options under CAD 1,500")
            self.assertEqual(len(sent), 3)
            self.assertEqual(len(sent[2]["actions"]), 3)

            code, sent = self.run_main(d, self.ENV, tp_rows=tp)
            self.assertEqual([m["title"] for m in sent], ["No new flight deals today"])
            self.assertIn("Caribbean & Mexico: cheapest CAD 610", sent[0]["message"])

    def test_feeds_only_without_any_keys(self):
        with tempfile.TemporaryDirectory() as d:
            code, sent = self.run_main(d, {"NTFY_TOPIC": "topic"})
            self.assertEqual(code, 0)
            self.assertEqual(len(sent), 1)
            self.assertTrue(sent[0]["title"].startswith("Sale post:"))

    def test_every_source_failing_warns(self):
        def boom(*a, **k):
            raise RuntimeError("Invalid API key")
        with tempfile.TemporaryDirectory() as d:
            code, sent = self.run_main(d, self.ENV, gf=boom, rss=b"not xml", tp_error=boom)
            self.assertEqual(code, 1)
            self.assertEqual(sent[-1]["title"], "Flight deals: every source failed")

    def test_partial_failure_still_succeeds(self):
        def boom(*a, **k):
            raise RuntimeError("quota used up")
        with tempfile.TemporaryDirectory() as d:
            code, _ = self.run_main(d, self.ENV, gf=boom)
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
