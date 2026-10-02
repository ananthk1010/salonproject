# ADR-0001: Stack — Next.js + FastAPI, two deploy targets

Status: Accepted (2026-09-25)

## Context

ABC-Salon Phase 1 needs a public demo, so needs a front end, a back end
that can call Jev and apply the policy, and a budget that fits free
hosting tiers. The owner proposed Next.js + TypeScript, Python + FastAPI,
Pydantic, and an OpenAPI-generated TypeScript contract.

## Decision

Accepted as proposed:

- **Front end**: Next.js (App Router), static export, deployed to Vercel
  Hobby. All data fetching is client-side against the API's own origin.
- **Back end**: Python 3.11 + FastAPI in Docker, deployed to Render Free.
  Python is the shared language with the offline lab (scikit-learn,
  AutoGluon), so the Jev client, rules, and policy modules are importable
  from both the API and `lab/jev_eval.py` without duplication.
- **Validation**: Pydantic v2 for every request/response model, the Jev
  question definitions, and the audit record.
- **Contract**: `apps/api/scripts/export_openapi.py` dumps the OpenAPI
  schema; `openapi-typescript` converts it to
  `packages/contracts/src/api.d.ts`. CI fails if the committed files are
  stale (see ADR context in architecture doc section 9.1).

## Alternative considered

Next.js API routes only, dropping FastAPI entirely. Rejected: the lab
(`lab/jev_eval.py`, the synthetic-data generator, the Mitra-v2 comparator)
is Python, and duplicating the Jev client, the tier rule, and the policy
rule in TypeScript just to avoid running two services was judged worse
than the two-origin deployment this stack requires.

## Consequences

Two deploy targets (Vercel + Render) instead of one, and a CORS
configuration between them. In exchange, `apps/web` and `lab/jev_eval.py`
both import the same `app.jev`, `app.rules`, and `app.policy` modules, so
the demo and the evaluation can never silently diverge in behaviour.
