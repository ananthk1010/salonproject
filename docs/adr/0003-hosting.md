# ADR-0003: Hosting — Vercel Hobby + Render Free

Status: Accepted (2026-09-25)

## Context

The project needs a shareable URL that costs nothing to run. Hugging Face
Docker Spaces, the owner's original proposal, was checked against its own
docs: "Gradio and Docker Spaces run on compute and require a paid plan to
create: PRO for personal accounts." Free personal accounts only get Static
Spaces and up to 2 ZeroGPU Gradio Spaces, neither of which fits a FastAPI
backend.

## Decision

- **Front end** (`apps/web`): Vercel Hobby. Free, and it is also where the
  Vercel AI Gateway key and budget live (ADR-0002).
- **API** (`apps/api`): Render Free web service, built from
  `apps/api/Dockerfile`. Verified limits: 512 MB RAM, 0.1 CPU, 750
  instance-hours/month, sleeps after 15 minutes idle and takes about a
  minute to wake.
- **Fallback**: Google Cloud Run's always-free tier (2M requests, 180k
  vCPU-seconds, 360k GiB-seconds/month) if Render turns out to require a
  card the owner would rather not add, or if 512 MB proves too tight.

## Consequences

- Two origins, so CORS must be configured (`CORS_ORIGINS` env var on the
  API, set to the Vercel production and preview domains).
- The API image must stay small: FastAPI, httpx, Pydantic, PyYAML, SQLite
  only. AutoGluon, PyTorch and scikit-learn live in `lab/requirements.txt`
  and are never installed in the deployed image.
- The UI polls `/api/health` and shows a "waking the API" banner
  (`apps/web/components/ApiStatusBanner.tsx`) to cover the Render cold
  start, rather than running an uptime pinger that would burn the 750 free
  instance-hours.
- The container's SQLite audit database is ephemeral (reset on redeploy
  or wake from sleep). Accepted for Phase 1; `GET /api/export/decisions`
  exists so the evaluation runner does not depend on the live database
  file surviving.
