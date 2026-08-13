# Deploying the ZDA Esoteric Engine

The site (React, Cloudflare Pages) calls this engine over HTTPS. The engine is
Python + C (`pyswisseph`), so it cannot run on Cloudflare Workers — it needs a
small container host. Fly.io is configured here; Railway/Render work the same way.

## One-time setup

```bash
# 1. Install the Fly CLI and sign in (opens a browser)
brew install flyctl && fly auth signup   # or: fly auth login
```

## Deploy

```bash
cd /Users/shannon/Documents/ZDA/Code/esoteric-engine
fly launch --no-deploy --copy-config --name zda-esoteric-engine --region yyz
fly secrets set API_KEY="$(openssl rand -hex 24)"
fly deploy
```

`fly deploy` builds the Dockerfile, which **runs the whole acceptance suite as a
build step** — 89 tests plus a 200-chart fuzz. A chart-engine regression fails the
build instead of shipping.

Grab the key you just generated (you'll paste it into Pages below):

```bash
fly secrets list        # confirms it's set
```

## Point the site at it

In Cloudflare Pages → your project → **Settings → Environment variables**, add:

| Name | Value |
|---|---|
| `VITE_ENGINE_URL` | `https://zda-esoteric-engine.fly.dev` |
| `VITE_ENGINE_KEY` | the API key from above |

Redeploy the Pages project so the build picks them up.

## Verify

```bash
curl https://zda-esoteric-engine.fly.dev/health
```

Expected — note this endpoint **recomputes the reference chart on every call** and
reports the error against the known-correct Ascendant, so a bad deploy is loud:

```json
{"status":"ok","ephemeris_backend":"moshier-builtin",
 "reference_chart_asc_error_arcmin":0.0013,"accuracy_check":"pass"}
```

If `status` is `degraded` or `accuracy_check` is `FAIL`, do not send traffic to it.

## Cost

`auto_stop_machines = "suspend"` with `min_machines_running = 0` means the machine
sleeps when idle and wakes on the first request (~1s cold start). At ZDA's traffic
this sits in Fly's free/low tier. Remove the suspend setting if the cold start
ever bothers you.

## Notes

- **Ephemeris backend.** The engine currently uses Swiss Ephemeris's built-in
  **Moshier** analytical model rather than the `.se1` data files — no data files
  are bundled. Accuracy is verified, not assumed: the acceptance suite matches
  Astro Gold to the arcminute and `/health` re-checks it on every call. If you
  ever bundle the data files, `/health` will report `swiss-files` and the
  accuracy check will confirm nothing moved.
- **Licence.** Shipping under Swiss Ephemeris's AGPL terms, so this engine repo
  is public. The platform layer (accounts, tiers, interpretation content) stays
  private and simply calls this API. See `SKYFIELD_EXPERIMENT.md` for the parked
  route to a fully permissive stack.
- **CORS** defaults to the ZDA domains plus localhost. Override with the
  `ALLOWED_ORIGINS` env var (comma-separated) if you add a staging domain.
