# ABC-Salon

A small salon-management app built to demonstrate [Jev](https://docs.typesafe.ai/introduction)
from TypeSafe AI — a model that returns typed, structured decisions
(choices, scores, probabilities, confidence) instead of free text.

This is a learning and portfolio project. All customer data is synthetic.
It is not affiliated with any real salon business.

**Status:** Phase 1 — Customer Classification and Jev Demonstration.
Built and passing locally; not yet deployed. See [Deploying](#deploying)
for what's left.

## What Phase 1 demonstrates

Jev classifies an incoming customer message — intent, service category,
urgency, frustration, and two speculative flags — with a probability
distribution and a confidence score for each answer.

A customer's **tier** (new / copper / bronze / silver / gold) is
deliberately **not** a Jev question. It's exact rupee-threshold arithmetic
on the customer's last visit spend, computed by a plain Python rule. That
split is the point of Phase 1: Jev is the right tool for judging an
ambiguous message, and the wrong tool for a decision that's already exact
math.

**Policy is one rule.** A `book_appointment` message is confirmed if it
arrives within the branch's opening hours, and auto-rejected otherwise.
Every other intent — reschedule, cancel, price enquiry, complaint,
feedback — is fully classified and recorded in the audit trail, but
creates no task. There's nothing to confirm or reject about a price
enquiry; the value there is the classification itself, which is what the
demo's decision panel shows.

Full design rationale, the technique-comparison argument (rules vs. Jev
vs. conventional ML), call flows, and every verified fact behind these
choices are in [`docs/ABC-Salon_Architecture_Design.docx`](docs/ABC-Salon_Architecture_Design.docx)
and [`docs/PHASE1_PLAN.md`](docs/PHASE1_PLAN.md).

## Architecture at a glance

```
apps/web      Next.js (TypeScript), static export — message picker,
              decision panel, confirmed-booking task board
apps/api      FastAPI (Python) — Jev client, rules, policy, audit trail
packages/contracts   OpenAPI schema + generated TypeScript types
eval/         Golden set + replay fixtures + evaluation results
lab/          Evaluation runner, offline ML comparisons (not deployed)
docs/         Plan, architecture document, ADRs
```

The API calls Jev through [Vercel AI Gateway's TypeSafe-compatible
endpoint](docs/adr/0002-jev-access-route.md) (TypeSafe's own direct signup
is currently closed). With no `JEV_API_KEY` set, or once a key's daily
budget is spent, the API serves recorded **replay fixtures** instead —
the public demo and CI both run this way by default, at zero cost.

## Quick start

### Docker (recommended)

```bash
docker compose up --build
```

Then open http://localhost:3010. The API is at http://localhost:8010.
Runs in replay mode by default — no API key needed to try it.

### Without Docker

```bash
# API
cd apps/api
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt   # .venv/bin/pip on macOS/Linux
.venv/Scripts/python scripts/generate_seed.py        # writes seed data + eval fixtures
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8010

# Web (separate terminal)
cd apps/web
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8010
npm install
npm run dev -- --port 3010
```

If `make` is available (it is in CI and on most Linux/macOS setups), the
[Makefile](Makefile) wraps all of the above: `make install`, `make seed`,
`make dev-api`, `make dev-web`, `make test`, `make eval`, `make contract`.

### Running against the real Jev (optional)

By default everything above runs in replay mode. To call the real
gateway, set in `apps/api`'s environment:

```
JEV_MODE=auto
JEV_API_KEY=<your Vercel AI Gateway key>
```

See [`docs/adr/0002-jev-access-route.md`](docs/adr/0002-jev-access-route.md)
for why it's the AI Gateway and not TypeSafe direct.

## Tests and evaluation

```bash
cd apps/api && .venv/Scripts/python -m pytest -q     # 50 tests: rules, policy, Jev client, API contract
python lab/jev_eval.py --mode replay                 # golden-set eval, writes eval/results.md
```

`eval/results.md` in replay mode is a harness sanity check, not a real
result — see [`eval/README.md`](eval/README.md) for why, and for how to
run it against the live gateway.

## Deploying

The code is ready to deploy; the accounts are not yet set up:

1. Push this repo to GitHub.
2. Deploy `apps/web` to Vercel (Hobby plan), with `NEXT_PUBLIC_API_URL`
   pointed at the API's Render URL.
3. Deploy `apps/api` to Render (Free plan) from `apps/api/Dockerfile`,
   build context = repo root. Set `JEV_API_KEY`, `JEV_BASE_URL`,
   `CORS_ORIGINS` (the Vercel domain).
4. Create an AI Gateway key in Vercel and purchase a small amount of
   credit (Jev is not in the gateway's free-tier model list) — see
   [`docs/adr/0002-jev-access-route.md`](docs/adr/0002-jev-access-route.md).

See [`docs/PHASE1_PLAN.md`](docs/PHASE1_PLAN.md) milestone M0/M2 for the
full checklist.

## Repository layout

See [`docs/ABC-Salon_Architecture_Design.docx`](docs/ABC-Salon_Architecture_Design.docx)
section 5 (container view) and section 10 (call flows) for the full
picture. Phase 2 (receptionist-assisted booking) and Phase 3
(self-service via WhatsApp) are documented but not built — see section 14
of the architecture document.

## Licence

MIT — see [LICENSE](LICENSE).
