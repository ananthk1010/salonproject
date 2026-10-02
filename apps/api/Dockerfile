# ABC-Salon API — Phase 1
# Slim image for Render Free's 512 MB RAM: FastAPI, httpx, Pydantic, PyYAML,
# SQLite only. No ML libraries here -- those live in lab/requirements.txt
# and never ship in this image (see docs/PHASE1_PLAN.md section 2.5).
#
# Build context MUST be the repo root (this Dockerfile needs the sibling
# eval/fixtures directory, not just apps/api/):
#   docker build -f apps/api/Dockerfile -t abc-salon-api .
# docker-compose.yml at the repo root is set up this way already.

FROM python:3.11-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/app ./app
COPY apps/api/data ./data

# Replay fixtures bundled into the image so the public demo works at zero
# cost with no live Jev key from the first deploy (see architecture doc
# section 11). FIXTURES_DIR overrides config.py's monorepo-relative default.
COPY eval/fixtures ./fixtures
ENV FIXTURES_DIR=/app/fixtures

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
