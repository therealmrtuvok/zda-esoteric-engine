"""
FastAPI service — thin JSON wrapper over the calculation modules.
Run with: uvicorn api.main:app --reload  (from the esoteric-engine/ root)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, model_validator
from datetime import date as DateType, datetime
from zoneinfo import ZoneInfo

from src.ephemeris_core import calc_chart
from src.astrology import format_natal_chart
from src.human_design import compute_hd_chart, hd_chart_to_dict
from src.numerology import numerology_report

app = FastAPI(title="ZDA Esoteric Engine", version="0.1.0")

# --- CORS -----------------------------------------------------------------
# Defaults to the ZDA origins + local dev. Override with ALLOWED_ORIGINS
# (comma-separated) in the host's env vars.
from fastapi.middleware.cors import CORSMiddleware

_DEFAULT_ORIGINS = [
    "https://zerodegreealchemy.com",
    "https://www.zerodegreealchemy.com",
    "http://localhost:5173",   # vite dev
    "http://localhost:8787",   # static preview
]
ALLOWED_ORIGINS = [
    o.strip() for o in
    os.environ.get("ALLOWED_ORIGINS", ",".join(_DEFAULT_ORIGINS)).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# --- API key --------------------------------------------------------------
# If API_KEY is set in the environment, every endpoint except /health and the
# docs requires a matching X-API-Key header. Unset (local dev) = open.
API_KEY = os.environ.get("API_KEY")
_OPEN_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc"}


# --- Rate limiting ---------------------------------------------------------
# A chart is a few hundred milliseconds of CPU. Without a cap, one script can
# keep the machine busy (and billable) indefinitely. In-memory and per-instance,
# which is the right size for this: it is a blunt abuse stop, not a quota system.
RATE_LIMIT_PER_MIN = int(os.environ.get("RATE_LIMIT_PER_MIN", "60"))
_hits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    # Fly and Cloudflare both put the real client first in X-Forwarded-For.
    fwd = request.headers.get("X-Forwarded-For") or request.headers.get("Fly-Client-IP")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    import time

    path = request.url.path
    if API_KEY and request.method != "OPTIONS" and path not in _OPEN_PATHS:
        if request.headers.get("X-API-Key") != API_KEY:
            return JSONResponse(status_code=401,
                                content={"detail": "invalid or missing X-API-Key"})

    if RATE_LIMIT_PER_MIN > 0 and request.method == "POST":
        now = time.monotonic()
        ip = _client_ip(request)
        window = [t for t in _hits.get(ip, []) if now - t < 60]
        if len(window) >= RATE_LIMIT_PER_MIN:
            retry = max(1, int(60 - (now - window[0])))
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry)},
                content={"detail": f"rate limit: {RATE_LIMIT_PER_MIN} requests/minute"})
        window.append(now)
        _hits[ip] = window
        # keep the dict from growing without bound on a long-lived instance
        if len(_hits) > 10_000:
            for k in [k for k, v in _hits.items() if not v or now - v[-1] > 120]:
                _hits.pop(k, None)

    return await call_next(request)


class NatalRequest(BaseModel):
    """
    Birth data. Two accepted shapes:

    1. Explicit parts + numeric UTC offset (original):
       {"year":1961,"month":8,"day":4,"hour":19,"minute":24,
        "timezone_offset_hours":-10,"latitude":21.3069,"longitude":-157.8583}

    2. ISO strings + IANA zone (preferred for front-ends):
       {"birth_date":"1961-08-04","birth_time":"19:24",
        "timezone":"Pacific/Honolulu","latitude":21.3069,"longitude":-157.8583}

    Shape 2 is safer: the engine resolves the historical UTC offset from the
    tz database, so daylight saving on the birth date is handled correctly.
    Getting EDT vs EST wrong shifts the Ascendant by roughly 15 degrees.
    """
    year: int | None = None
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minute: int | None = None
    timezone_offset_hours: float | None = None
    latitude: float
    longitude: float

    # Alternate input form
    birth_date: str | None = None      # "YYYY-MM-DD"
    birth_time: str | None = None      # "HH:MM" (24h)
    timezone: str | None = None        # IANA, e.g. "America/Toronto"

    @model_validator(mode="after")
    def _normalise(self):
        # Date/time strings → parts
        if self.birth_date:
            try:
                y, m, d = (int(p) for p in self.birth_date.split("-"))
            except ValueError:
                raise ValueError("birth_date must be YYYY-MM-DD")
            self.year, self.month, self.day = y, m, d
        if self.birth_time:
            try:
                hh, mm = (int(p) for p in self.birth_time.split(":")[:2])
            except ValueError:
                raise ValueError("birth_time must be HH:MM (24-hour)")
            self.hour, self.minute = hh, mm

        missing = [n for n in ("year", "month", "day")
                   if getattr(self, n) is None]
        if missing:
            raise ValueError(
                f"missing {', '.join(missing)} — supply either birth_date "
                f"('YYYY-MM-DD') or explicit year/month/day"
            )
        if self.hour is None:
            self.hour = 12          # unknown birth time → noon
        if self.minute is None:
            self.minute = 0

        # IANA zone → the UTC offset actually in force on that date
        if self.timezone_offset_hours is None:
            if not self.timezone:
                raise ValueError(
                    "supply either timezone_offset_hours (number) or "
                    "timezone (IANA name, e.g. 'America/Toronto')"
                )
            try:
                tz = ZoneInfo(self.timezone)
            except Exception:
                raise ValueError(f"unknown IANA timezone {self.timezone!r}")
            local = datetime(self.year, self.month, self.day,
                             self.hour, self.minute, tzinfo=tz)
            self.timezone_offset_hours = local.utcoffset().total_seconds() / 3600

        return self


class NumerologyRequest(BaseModel):
    birth_year: int
    birth_month: int
    birth_day: int
    today_year: int | None = None
    today_month: int | None = None
    today_day: int | None = None


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    """
    Liveness + an accuracy self-check. Recomputes the public reference chart
    (1961-08-05 05:24 UT, Honolulu — Rodden AA, see tests/) and compares against
    its known-correct Ascendant. A deploy where the ephemeris backend changed or
    data files went missing reports degraded here instead of silently serving
    wrong charts.
    """
    import swisseph as swe
    from src.ephemeris_core import _EPHE_PATH

    try:
        swe.set_ephe_path(_EPHE_PATH)
        jd = swe.julday(1961, 8, 5, 5 + 24 / 60)
        _r, flag = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
        backend = ("swiss-files" if flag & swe.FLG_SWIEPH
                   else "moshier-builtin" if flag & swe.FLG_MOSEPH
                   else f"unknown({flag})")

        chart = calc_chart(1961, 8, 5, 5 + 24 / 60, 21.3069, -157.8583)
        asc_err_arcmin = abs(chart.ascendant - 318.0518) * 60
        ok = asc_err_arcmin < 1.0
        return {
            "status": "ok" if ok else "degraded",
            "ephemeris_backend": backend,
            "reference_chart_asc_error_arcmin": round(asc_err_arcmin, 4),
            "accuracy_check": "pass" if ok else "FAIL",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ephemeris unavailable: {e}")


@app.post("/natal/astrology")
def natal_astrology(req: NatalRequest):
    hour_ut = req.hour + req.minute / 60 - req.timezone_offset_hours
    try:
        chart = calc_chart(req.year, req.month, req.day, hour_ut,
                           req.latitude, req.longitude)
        return format_natal_chart(chart)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/natal/human-design")
def natal_hd(req: NatalRequest):
    hour_ut = req.hour + req.minute / 60 - req.timezone_offset_hours
    try:
        hd = compute_hd_chart(req.year, req.month, req.day, hour_ut,
                              req.latitude, req.longitude)
        return hd_chart_to_dict(hd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/numerology")
def numerology(req: NumerologyRequest):
    birth = DateType(req.birth_year, req.birth_month, req.birth_day)
    today = None
    if req.today_year and req.today_month and req.today_day:
        today = DateType(req.today_year, req.today_month, req.today_day)
    return numerology_report(birth, today)


# ---------------------------------------------------------------------------
# Derived chart endpoints (addendum Part 2)
# ---------------------------------------------------------------------------
from src.ephemeris_core import julian_day, jd_to_datetime_tuple
from src.astrology import longitude_to_sign_degree, planet_sign_str
from src.derived_charts import (
    progressed_positions, solar_return, lunar_return, annual_profection,
    synastry_aspects, composite_positions, transit_aspects_to_natal,
)
from src.hd_connection import connection_chart, hd_transit_overlay


class TargetDateRequest(NatalRequest):
    target_year: int
    target_month: int
    target_day: int


class PairRequest(BaseModel):
    person_a: NatalRequest
    person_b: NatalRequest


def _hour_ut(req: NatalRequest) -> float:
    return req.hour + req.minute / 60 - req.timezone_offset_hours


def _positions_dict(chart):
    return {name: {"longitude": p.longitude, "speed": p.speed,
                   "retrograde": p.retrograde}
            for name, p in chart.planets.items()}


def _label_positions(positions: dict) -> dict:
    out = {}
    for name, p in positions.items():
        sign, deg = longitude_to_sign_degree(p["longitude"])
        out[name] = {**p, "sign": sign, "degree_in_sign": round(deg, 3),
                     "display": planet_sign_str(p["longitude"],
                                                p.get("retrograde", False))}
    return out


@app.post("/progressions")
def progressions(req: TargetDateRequest):
    birth_jd = julian_day(req.year, req.month, req.day, _hour_ut(req))
    target_jd = julian_day(req.target_year, req.target_month, req.target_day, 12)
    prog = progressed_positions(birth_jd, target_jd)
    return {
        "elapsed_years": round(prog["elapsed_years"], 3),
        "positions": _label_positions(prog["positions"]),
    }


@app.post("/solar-return")
def solar_return_endpoint(req: TargetDateRequest):
    natal = calc_chart(req.year, req.month, req.day, _hour_ut(req),
                       req.latitude, req.longitude)
    return_jd, chart = solar_return(natal.planets["sun"].longitude,
                                    req.target_year, req.latitude, req.longitude,
                                    req.month, req.day)
    y, m, d, h = jd_to_datetime_tuple(return_jd)
    return {
        "return_datetime_ut": f"{y:04d}-{m:02d}-{d:02d} {int(h):02d}:{int(h%1*60):02d} UT",
        "chart": format_natal_chart(chart),
    }


@app.post("/lunar-return")
def lunar_return_endpoint(req: TargetDateRequest):
    natal = calc_chart(req.year, req.month, req.day, _hour_ut(req),
                       req.latitude, req.longitude)
    from_jd = julian_day(req.target_year, req.target_month, req.target_day, 0)
    return_jd, chart = lunar_return(natal.planets["moon"].longitude, from_jd,
                                    req.latitude, req.longitude)
    y, m, d, h = jd_to_datetime_tuple(return_jd)
    return {
        "return_datetime_ut": f"{y:04d}-{m:02d}-{d:02d} {int(h):02d}:{int(h%1*60):02d} UT",
        "chart": format_natal_chart(chart),
    }


@app.post("/profection")
def profection(req: TargetDateRequest):
    natal = calc_chart(req.year, req.month, req.day, _hour_ut(req),
                       req.latitude, req.longitude)
    return annual_profection(
        natal.ascendant,
        DateType(req.year, req.month, req.day),
        DateType(req.target_year, req.target_month, req.target_day),
    )


@app.post("/synastry")
def synastry(req: PairRequest):
    a = calc_chart(req.person_a.year, req.person_a.month, req.person_a.day,
                   _hour_ut(req.person_a), req.person_a.latitude, req.person_a.longitude)
    b = calc_chart(req.person_b.year, req.person_b.month, req.person_b.day,
                   _hour_ut(req.person_b), req.person_b.latitude, req.person_b.longitude)
    pa, pb = _positions_dict(a), _positions_dict(b)
    return {
        "aspects": synastry_aspects(pa, pb),
        "composite_positions": _label_positions(composite_positions(pa, pb)),
    }


@app.post("/connection")
def connection(req: PairRequest):
    a = compute_hd_chart(req.person_a.year, req.person_a.month, req.person_a.day,
                         _hour_ut(req.person_a), req.person_a.latitude, req.person_a.longitude)
    b = compute_hd_chart(req.person_b.year, req.person_b.month, req.person_b.day,
                         _hour_ut(req.person_b), req.person_b.latitude, req.person_b.longitude)
    return connection_chart(a, b)


@app.post("/transits")
def transits(req: TargetDateRequest):
    natal = calc_chart(req.year, req.month, req.day, _hour_ut(req),
                       req.latitude, req.longitude)
    jd = julian_day(req.target_year, req.target_month, req.target_day, 12)
    astro = transit_aspects_to_natal(_positions_dict(natal), jd)
    hd = compute_hd_chart(req.year, req.month, req.day, _hour_ut(req),
                          req.latitude, req.longitude)
    overlay = hd_transit_overlay(hd, jd)
    return {
        "astrology": {
            "transiting": _label_positions(astro["transiting"]),
            "aspects_to_natal": astro["aspects"],
        },
        "human_design": overlay,
    }


# ---------------------------------------------------------------------------
# Transit overlay + projection endpoints (addendum 2)
# ---------------------------------------------------------------------------
from src.hd_transit import transit_state, scan_channel_windows, ALL_BODIES, SLOW_BODIES


class TransitStateRequest(NatalRequest):
    target_year: int
    target_month: int
    target_day: int
    target_hour: int = 12
    target_minute: int = 0
    bodies: list[str] | None = None   # default: all bodies


class ProjectionRequest(NatalRequest):
    range_start_year: int
    range_start_month: int
    range_start_day: int
    range_end_year: int
    range_end_month: int
    range_end_day: int
    bodies: list[str] | None = None   # default: slow bodies only


@app.post("/transit-state")
def transit_state_endpoint(req: TransitStateRequest):
    hd = compute_hd_chart(req.year, req.month, req.day, _hour_ut(req),
                          req.latitude, req.longitude)
    jd = julian_day(req.target_year, req.target_month, req.target_day,
                    req.target_hour + req.target_minute / 60)
    state = transit_state(hd, jd, bodies=req.bodies)
    state["natal"] = {
        "type": hd.type_, "profile": hd.profile, "authority": hd.authority,
        "definition": hd.definition,
        "defined_channels": sorted(hd.defined_channels),
    }
    # per-gate natal source detail for two-color rendering
    return state


@app.post("/projection")
def projection(req: ProjectionRequest):
    hd = compute_hd_chart(req.year, req.month, req.day, _hour_ut(req),
                          req.latitude, req.longitude)
    jd_start = julian_day(req.range_start_year, req.range_start_month,
                          req.range_start_day, 12)
    jd_end = julian_day(req.range_end_year, req.range_end_month,
                        req.range_end_day, 12)
    if jd_end - jd_start > 366 * 12:
        raise HTTPException(status_code=400, detail="range too large (max 12 years)")
    windows = scan_channel_windows(hd, jd_start, jd_end, bodies=req.bodies)
    for w in windows:
        w.pop("start_jd", None)
        w.pop("end_jd", None)
    return {"windows": windows,
            "bodies": req.bodies or SLOW_BODIES}


# ---------------------------------------------------------------------------
# Interpretation layer — meaning attached to computed facts.
# Kept behind its own endpoint so the calculation endpoints stay pure data.
# ---------------------------------------------------------------------------
from src.interpretations import interpret_chart


@app.post("/interpret")
def interpret(req: NatalRequest):
    """Full chart plus interpretation text, in one call."""
    hour_ut = req.hour + req.minute / 60 - req.timezone_offset_hours
    try:
        hd = hd_chart_to_dict(compute_hd_chart(
            req.year, req.month, req.day, hour_ut, req.latitude, req.longitude))
        num = numerology_report(DateType(req.year, req.month, req.day))
        return {
            "human_design": hd,
            "numerology": num,
            "interpretation": interpret_chart(human_design=hd, numerology=num),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
