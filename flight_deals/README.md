# Flight deal watcher

Searches Google Flights (through [SerpApi](https://serpapi.com/google-flights-api)) for
the routes in `config.toml`, and pushes a phone notification through
[ntfy](https://ntfy.sh) when a fare is a deal. Runs once a day on GitHub Actions.
Standard library only (Python 3.11+); unrelated to the engine in the rest of this repo.

A fare is a **deal** when the cheapest option is at or under the route's `max_price`,
**or** Google Flights rates the price "low" for that route (`alert_on_google_low`).
Each deal is pushed once; it's pushed again only if the price drops another
`realert_drop_pct` percent. The notification opens the search in Google Flights.

## Setup

1. **SerpApi key**: sign up at serpapi.com and copy your API key from the dashboard.
2. **ntfy**: install the ntfy app (iOS/Android) and subscribe to a topic with a long,
   unguessable name, e.g. `flights-7f3k9q2xw`. Anyone who knows the name can read
   it, so treat it like a password.
3. **Repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `SERPAPI_KEY`: your SerpApi key
   - `NTFY_TOPIC`: your topic name
   - `NTFY_TOKEN`: optional, only if you use a protected topic on your own ntfy server
4. **Edit `config.toml`**: the routes in it are placeholders (Boston to Lisbon/Tokyo).
5. **Check it**: Actions tab → "Flight deals" → *Run workflow*.

Until both secrets are set, the scheduled job does nothing and passes.

## Watching your search budget

Each (departure date × trip length) is one SerpApi search. `python deals.py --dry-run`
lists them without spending any. Monthly usage is about
`searches per run × runs per day × 30`; the example config is 3 × 1 × 30 = 90.
Check your SerpApi plan's monthly allowance. `max_searches_per_run` is a hard cap.
The cron schedule is in `.github/workflows/flight-deals.yml`.

If every search in a run fails (bad key, quota used up), you get a warning push
instead of silence.

## Running locally

```sh
export SERPAPI_KEY=... NTFY_TOPIC=...
python flight_deals/deals.py --test-notify   # check the phone gets a push
python flight_deals/deals.py --no-notify     # search and print, no push, no state saved
python flight_deals/deals.py                 # the real thing
python -m unittest flight_deals/test_deals.py
```

Alert history is kept in `flight_deals/state.json` (gitignored; on Actions it lives
in the Actions cache).
