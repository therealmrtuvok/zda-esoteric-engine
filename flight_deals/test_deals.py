"""Tests for the flight deal watcher. Run: python -m unittest flight_deals/test_deals.py"""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deals  # noqa: E402

TODAY = date(2026, 11, 1)


def route(**kw):
    base = dict(name="BOS-LIS", origin="BOS", destination="LIS", depart_in_days=[30], max_price=500)
    base.update(kw)
    return deals.Route(**base)


def response(prices, level=None, typical=None):
    def option(p):
        return {"price": p, "total_duration": 425,
                "flights": [{"airline": "TAP Air Portugal"}, {"airline": "TAP Air Portugal"}]}
    data = {"best_flights": [option(p) for p in prices[:1]],
            "other_flights": [option(p) for p in prices[1:]],
            "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights?x"}}
    if level:
        data["price_insights"] = {"price_level": level, "typical_price_range": typical or [600, 900]}
    return data


class PlanSearches(unittest.TestCase):
    def test_round_trip_expands_dates_and_nights(self):
        s = deals.plan_searches([route(depart_in_days=[30, 60], nights=[7, 10])], TODAY)
        self.assertEqual([x.key for x in s], [
            "BOS-LIS|2026-12-01|2026-12-08", "BOS-LIS|2026-12-01|2026-12-11",
            "BOS-LIS|2026-12-31|2027-01-07", "BOS-LIS|2026-12-31|2027-01-10"])

    def test_oneway_and_past_fixed_dates_dropped(self):
        r = route(trip="oneway", depart_in_days=[], depart_dates=["2026-10-01", "2026-12-24"])
        self.assertEqual([x.key for x in deals.plan_searches([r], TODAY)], ["BOS-LIS|2026-12-24|oneway"])

    def test_routes_are_interleaved_so_the_cap_covers_all(self):
        a = route(name="a", depart_in_days=[10, 20, 30])
        b = route(name="b", origin="JFK", depart_in_days=[10])
        names = [x.route.name for x in deals.plan_searches([a, b], TODAY)]
        self.assertEqual(names, ["a", "b", "a", "a"])


class FindDeal(unittest.TestCase):
    def search(self, **kw):
        return deals.plan_searches([route(**kw)], TODAY)[0]

    def test_cheapest_under_limit_is_a_deal(self):
        d = deals.find_deal(self.search(), response([640, 480, 520]))
        self.assertEqual(d.price, 480)
        self.assertEqual(d.airlines, ["TAP Air Portugal"])
        self.assertEqual(d.stops, 1)

    def test_over_limit_and_not_low_is_not_a_deal(self):
        self.assertIsNone(deals.find_deal(self.search(), response([620], level="typical")))

    def test_google_low_triggers_even_over_limit(self):
        d = deals.find_deal(self.search(), response([620], level="low"))
        self.assertEqual(d.reasons, ["Google rates this price low"])

    def test_google_low_ignored_when_disabled(self):
        s = self.search(alert_on_google_low=False)
        self.assertIsNone(deals.find_deal(s, response([620], level="low")))

    def test_empty_results(self):
        self.assertIsNone(deals.find_deal(self.search(), {"best_flights": []}))


class Dedupe(unittest.TestCase):
    def test_realert_only_on_meaningful_drop(self):
        s = deals.plan_searches([route()], TODAY)[0]
        state = {s.key: {"price": 500}}
        deal = deals.find_deal(s, response([460]))
        self.assertFalse(deals.is_new(deal, state, 10))   # 8% cheaper
        deal = deals.find_deal(s, response([450]))
        self.assertTrue(deals.is_new(deal, state, 10))    # 10% cheaper

    def test_past_departures_are_pruned(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            p.write_text(json.dumps({"BOS-LIS|2026-10-01|oneway": {"price": 1},
                                     "BOS-LIS|2026-12-01|2026-12-08": {"price": 2}}))
            self.assertEqual(list(deals.load_state(p, TODAY)), ["BOS-LIS|2026-12-01|2026-12-08"])


class Config(unittest.TestCase):
    def test_shipped_config_loads(self):
        settings, routes = deals.load_config(Path(deals.HERE) / "config.toml")
        self.assertTrue(routes)
        self.assertEqual(routes[1].nights, [12])

    def test_bad_stops_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('[[routes]]\nname="x"\nfrom="A"\nto="B"\ndepart_in_days=[5]\nstops="3"\n')
        with self.assertRaises(ValueError):
            deals.load_config(Path(f.name))


class EndToEnd(unittest.TestCase):
    def test_run_alerts_once_then_stays_quiet(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "config.toml"
            cfg.write_text('[[routes]]\nname="Lisbon"\nfrom="BOS"\nto="LIS"\n'
                           'depart_in_days=[30]\nnights=7\nmax_price=500\n')
            state = Path(d) / "state.json"
            argv = ["--config", str(cfg), "--state", str(state)]
            with mock.patch.dict("os.environ", {"SERPAPI_KEY": "k", "NTFY_TOPIC": "t"}), \
                 mock.patch.object(deals, "fetch", return_value=response([450])), \
                 mock.patch.object(deals, "ntfy_send") as send:
                self.assertEqual(deals.main(argv), 0)
                self.assertEqual(send.call_count, 1)
                title, body = send.call_args.args
                self.assertEqual(title, "Lisbon: USD 450")
                self.assertIn("1 stop", body)
                self.assertEqual(send.call_args.kwargs["click"], "https://www.google.com/travel/flights?x")
                self.assertEqual(deals.main(argv), 0)
                self.assertEqual(send.call_count, 1)   # same deal, not re-sent

    def test_all_searches_failing_sends_warning(self):
        with tempfile.TemporaryDirectory() as d:
            argv = ["--state", str(Path(d) / "state.json")]
            with mock.patch.dict("os.environ", {"SERPAPI_KEY": "k", "NTFY_TOPIC": "t"}), \
                 mock.patch.object(deals, "fetch", side_effect=RuntimeError("Invalid API key")), \
                 mock.patch.object(deals, "ntfy_send") as send:
                self.assertEqual(deals.main(argv), 1)
                self.assertIn("every search failed", send.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
