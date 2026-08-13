FROM python:3.12-slim

WORKDIR /app

# pyswisseph builds from source on slim images and has BOTH C and C++ sources
# (swephelp/swhdbxx.cpp), so gcc alone is not enough — g++ is required.
# build-essential covers both; it is purged afterwards so it doesn't ship.
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential python3-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y build-essential python3-dev \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Asteroid ephemeris. Chiron and Juno CANNOT be computed by the built-in
# Moshier model — they require this data file. Locally it comes from
# kerykeion's bundled sweph directory; in the image it must ship explicitly.
# Main planets still fall back to Moshier, which /health verifies.
COPY data/ephe/ ./data/ephe/
ENV EPHE_PATH=/app/data/ephe

COPY src/ ./src/
COPY api/ ./api/
COPY tests/ ./tests/

# Fail the build if the engine's own acceptance suite doesn't pass.
# A broken chart engine must never reach production.
RUN python tests/test_acceptance_astrology.py \
 && python tests/test_acceptance_hd.py \
 && python tests/test_acceptance_numerology.py \
 && python tests/test_acceptance_derived.py \
 && python tests/test_acceptance_transit.py \
 && python tests/test_crosses.py \
 && python tests/test_invariants.py \
 && python tests/test_fixtures.py \
 && python tests/test_interpretations.py \
 && FUZZ_N=200 python tests/test_fuzz.py

# Prove the app imports and the reference chart is still correct inside the
# image (no HTTP client needed — call the health handler directly).
RUN python -c "\
import sys; sys.path.insert(0, '.');\
from api.main import health;\
d = health();\
print('health:', d);\
sys.exit(0 if d.get('accuracy_check') == 'pass' else 1)"

ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
