# Flight deal watcher

Watches for flights for one trip (set in `config.toml`; currently Toronto, New
Year's 2026–27, to the Caribbean & Mexico, Central & South America, or Europe,
under CA$1,500) and pushes what it finds to your phone with
[ntfy](https://ntfy.sh). Runs daily on GitHub Actions. Standard library only
(Python 3.11+); unrelated to the engine in the rest of this repo.

## Sources

| Source | What it finds | Needs |
|---|---|---|
| **Google Flights** via [SerpApi](https://serpapi.com/google-flights-api) | Live prices for your exact dates. One search covers a whole region (up to 7 airports). | `SERPAPI_KEY` |
| **[Travelpayouts](https://www.travelpayouts.com)** (Aviasales data) | Cheapest fares from your city to *anywhere* that other travellers saw recently. Good for discovering destinations. Prices can be stale. | `TRAVELPAYOUTS_TOKEN` |
| **Deal-site feeds** (Flytrippers, The Flight Deal, Fly4free, r/flightdeals) | Sale and error-fare posts that mention your city, a region, the holidays and a price within budget. | nothing |

Each source runs only when its key is set, so the feeds work with no setup at
all. It deliberately does **not** scrape airline or booking sites: their terms
forbid it, and they block it within days. YYZ Deals and Secret Flying block
automated readers too, so subscribe to their emails directly.

## What you get on your phone

- **DEAL: Cancún CAD 610**: a fare at or under the region's `deal_price`, or
  one Google rates "low". High priority, one push each, tap to open.
- **Sale post: …**: a matching deal-site post. Check that it covers your dates.
- **7 new options under CAD 1,500**: everything else within budget, in one digest.
- **No new flight deals today**: a silent daily summary with the cheapest fare
  per region, so you can watch the trend.
- **Every source failed**: if a key is wrong or a quota is used up.

Each find is pushed once, and again only if it gets 10% cheaper.

## Setup

1. **ntfy**: install the ntfy app and subscribe to a long, unguessable topic name.
2. **SerpApi**: sign up at serpapi.com and copy your API key.
3. **Travelpayouts**: sign up at travelpayouts.com, then copy your API token
   from the Developers / API section of your profile.
4. **Repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   `NTFY_TOPIC`, `SERPAPI_KEY`, `TRAVELPAYOUTS_TOKEN`.
5. The daily schedule only runs from the default branch, so this needs to be merged to `main`.

To check it right away, go to the Actions tab, open "Flight deals" and click
*Run workflow*. It also re-runs whenever this folder changes.

## Budget

Google Flights searches: `len(google_trips) × regions` per run, so 2 × 3 = 6 a day,
about 180 a month. Check that against your SerpApi plan. `python flight_deals/deals.py --dry-run`
lists them without spending any. Travelpayouts and the feeds are free.

## Running locally

```sh
export SERPAPI_KEY=... TRAVELPAYOUTS_TOKEN=... NTFY_TOPIC=...
python flight_deals/deals.py --test-notify   # check the phone gets a push
python flight_deals/deals.py --no-notify     # check and print only
python flight_deals/deals.py                 # the real thing
python -m unittest flight_deals/test_deals.py
```

## Next trip

Edit `[trip]` in `config.toml`: dates, budget and `google_trips`. Regions,
airports and feeds can stay. After the latest departure date passes, the
watcher stops checking and says so in its log.
