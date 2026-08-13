FROM python:3.12-slim

WORKDIR /app

# pyswisseph is a C extension. Manylinux wheels usually cover this, but if pip
# has to build from source the image needs a compiler — install one, then drop
# it so it doesn't ship in the final image.
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc python3-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y gcc python3-dev \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

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
