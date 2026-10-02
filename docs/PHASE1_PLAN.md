# ABC-Salon — Phase 1 Plan: Customer Classification and Jev Demonstration

Status: DRAFT v3 (2026-09-30). Supersedes v2 (2026-09-25).
Owner: Ananth Kollipara (github.com/ananthk1010)
Scope: Phase 1 only. Phase 2/3 get an architecture note at the end of Phase 1, not code.

Decisions taken on 2026-09-25 (by the owner):
- Stack: Next.js + TypeScript front end, Python + FastAPI back end, Pydantic, OpenAPI-generated TypeScript types, Docker.
- Hosting: front end on Vercel Hobby, API container on a free-tier container host (Render Free selected below, with Cloud Run as fallback).
- Jev access: Vercel AI Gateway with purchased credits, because TypeSafe direct signup is disabled.

Decisions taken on 2026-09-30 (by the owner), which this revision implements:
- **Tier is a deterministic rule, not a Jev question.** Five bands by the customer's last visit spend in rupees (₹), fully specified by the owner. Jev is never asked to classify the customer; it classifies the message.
- **The `mentions_medical` Jev question is removed.** It did not map cleanly to a salon context.
- **Policy is reduced to one rule for Phase 1**: a `book_appointment` message is confirmed if it arrives within the branch's opening hours, and auto-rejected otherwise. Every other intent (reschedule, cancel, price enquiry, complaint, feedback, other) is classified by Jev and fully recorded in the audit trail, but creates no task and is not rejected — there is nothing to accept or reject about a price enquiry.
- **Confidence-gated routing is removed from Phase 1 entirely.** Confidence is still computed, shown in the UI, and stored in every Decision — that is the Jev demonstration — but nothing in Phase 1's routing reads it.
- **The Strands optional track is deferred to Phase 2 in full**, including the lab walkthrough. It existed only to act on an escalated task, and Phase 1 no longer produces escalated tasks once confidence-gating and the medical gate are gone. Reintroducing escalation, the medical safety check, and the Manager Assistant are now Phase 2 proposals; see section 13.

---

## 1. What Phase 1 delivers

| # | Deliverable (from the brief) | Phase 1 concrete output |
|---|---|---|
| 1 | Immediately viewable interactive demo | Public web app: pick or paste a customer message, see Jev's typed decisions, probabilities, confidence, and the outcome (confirmed / rejected / recorded) |
| 2 | Concise technical whitepaper | `docs/WHITEPAPER.md` (6–8 pages): problem, rules vs Jev vs conventional ML, evaluation results, lessons |
| 3 | Public source-code repository | `github.com/ananthk1010/abc-salon`, MIT licence, CI running lint, unit tests, contract check, eval in replay mode |
| 4 | Architecture and workflow docs | `docs/ARCHITECTURE.md` (C4 diagrams in Mermaid), `docs/WORKFLOW.md` (sequence diagrams), ADRs in `docs/adr/` |
| 5 | Shareable URL | Front end on Vercel; API as a Docker image on Render Free; keys held server-side only |
| 6 | LinkedIn-ready description and post | `docs/LINKEDIN.md`: 150-word project blurb, one showcase post, 3 screenshots or a GIF |

---

## 2. Verified facts that shape the design (checked 2026-09-24 and 2026-09-25)

### 2.1 Jev (TypeSafe AI)

- Native endpoint: `POST https://api.typesafe.ai/v1/systemone`, bearer key, model `jev-latest`.
- Input: one `state` (string, object, or array) plus a map of typed `questions`. Every question is evaluated independently and in parallel against the same state.
- Primitives: `choice` (map of option to description, up to 255 options; returns `choice`, `probabilities`, `confidence`), `score` (2 to 10 ordered level descriptions; returns fractional `score`, `legend`, `probabilities`, `confidence`), `noul` (yes/no statement; returns `noul` in 0 to 1, no confidence field).
- `confidence` is a statistic of how peaked the probability distribution is. In Phase 1 it is computed and displayed for every answer, but does not drive any routing decision — see section 4.
- Limits: 64k tokens per request, 32k for `state`. Errors: 401, 422, 429, 529.
- SDKs: `typesafe-sdk` 0.7.1 (Python 3.10+, MIT, sync and async clients, no documented custom base URL), `@typesafe-ai/sdk` (Node 20+, accepts `baseURL`).
- Price: $0.042 per 1M input tokens, output free. A 1,500-token state with 6 questions costs a fraction of a cent.
- Not for: text generation, chatbots, copilots, multi-step reasoning, or classifying the customer — see the tier decision in section 4.

### 2.2 Access route: Vercel AI Gateway (decided)

Direct signup at console.typesafe.ai returned `signups_disabled` on 2026-09-25. Third-party reports say signups paused on 2026-09-22; no reopening date is published.

Verified facts about the chosen route:
- Vercel docs (updated 2026-09-21) publish a TypeSafe-compatible API: base URL `https://ai-gateway.vercel.sh/typesafe`, endpoint `POST /v1/systemone`, model id `typesafe-ai/jev`, auth `Authorization: Bearer <AI Gateway API key>`. Request and response use TypeSafe's own field names. An official Python `requests` example exists.
- AI Gateway charges no markup; Jev bills at $0.04 per 1M input tokens through it. Jev is NOT in the gateway's free-tier model subset, so AI Gateway Credits must be purchased. The minimum top-up amount is not published in the docs; it will be visible in the dashboard at purchase time. Buying credits ends the $5 monthly free allowance for other models, which we do not need.
- The gateway also offers a native `/v1/evaluate` endpoint that renames `noul` to `boolean` with a `probability` field and camel-cases `usage`. We do not use it, to keep the code portable to TypeSafe direct.
- Budgets can be capped per team, project or API key in the Vercel dashboard. Set one before the demo goes public.
- Unverified until the M1 spike: whether the gateway's TypeSafe-compatible response includes `confidence` for `choice` and `score` answers (the Vercel example shows only a `noul` answer). If missing, compute it in code from `probabilities` using TypeSafe's published definition, and record the fact in the whitepaper.

Other routes, kept as documented fallbacks: Cloudflare Workers AI lists `typesafe/jev` with the native shape, but its price and free-plan inclusion are unverified. OpenRouter's Jev page returned 404. TypeSafe direct: re-check weekly; switching is one env var.

Implementation: `app/jev/client.py`, a small `httpx` client (about 40 lines) against the documented request shape, configured by `JEV_BASE_URL`, `JEV_API_KEY`, `JEV_MODEL`. The Python `typesafe-sdk` is not used because it has no documented base URL override.

### 2.3 Amazon Mitra-v2 (unchanged from v1)

Tabular foundation model from the AutoGluon team, Apache-2.0, `autogluon/mitra-classifier-2`, 75.7M parameters, in-context learning, CPU or GPU via `autogluon.tabular[mitra] >= 1.6`. Limits 10,000 rows, 500 features, 10 classes. Needs labelled rows; cannot read text.

Verdict: irrelevant for message intent, urgency, or sentiment — and, per the 2026-09-30 decision, also not used for tier, which is exact arithmetic and stays a deterministic rule. Relevant as a comparator for churn risk from visit history on a synthetic labelled table. Kept as a stretch item in the offline Python lab next to a logistic-regression baseline that always runs. Never installed in the API image (512 MB RAM on Render Free). All docs must state the data is synthetic.

### 2.4 Strands Harness (AWS) — findings, deferred to Phase 2

Verified from `github.com/strands-agents/harness-sdk`, `strandsagents.com/docs/user-guide/harness/`, and PyPI:

- Released 2026-09-21, Apache-2.0. Monorepo holds `strands-harness` (Python 3.10+, `pip install strands-harness`), `@strands-agents/harness` (Node 22+), the lower-level `strands-agents` SDK, and a CLI.
- `create_harness()` returns a standard Strands Agent pre-wired with shell, file (read/write/edit) and web tools, a task checklist, long-term memory across runs, a helper sub-agent, prompt caching and context management. Every default is overridable.
- It needs an LLM. Providers: Amazon Bedrock (default), Anthropic, OpenAI, Google, Ollama, LiteLLM. Jev cannot be its model; Jev does not generate text.
- AWS positions it as a general-purpose autonomous agent, reporting about 28% lower token cost than comparable harnesses.

Status as of 2026-09-30: not part of Phase 1, including the lab walkthrough. The only place a Strands agent had a job was drafting a proposal on an escalated task, and Phase 1 no longer escalates anything — there is no confidence gate and no medical gate to trigger it. Reintroducing escalation is a Phase 2 decision; see section 13.

### 2.5 Hosting facts

| Host | Verified on 2026-09-25 | Decision |
|---|---|---|
| Hugging Face Docker Space | Requires a paid plan (PRO) for personal accounts; free accounts get Static Spaces and up to 2 ZeroGPU Gradio Spaces | Not used |
| Vercel Hobby | Free; hosts the Next.js front end; also holds the AI Gateway key and budget | Front end |
| Render Free web service | 512 MB RAM, 0.1 CPU, 750 instance-hours per month per workspace, spins down after 15 minutes idle and takes roughly a minute to wake, custom domains allowed, Dockerfile builds supported. Whether a card is required was not stated in the docs; confirm at signup | API container (primary) |
| Google Cloud Run | Always-free: 2M requests, 180k vCPU-seconds, 360k GiB-seconds, 1 GB North America egress per month; scale to zero; a billing account with a card is required | API container (fallback if Render needs a card or 512 MB is too small) |
| Fly.io | No free tier; card required; smallest machine about $2 per month | Not used |

Consequences: the UI must show a "waking up the API" state for the Render cold start. The API image must stay small (FastAPI, httpx, pydantic, sqlite; no ML libraries).

### 2.6 Reference salon (public site, structure only)

Generic concepts: service menu grouped by hair, skin, spa/body, and treatments; several branches in one city; phone or online appointment requests. ABC-Salon uses fictional branch names and generic service names. No text, images, prices or branding are copied.

---

## 3. Stack, with trade-offs

| Layer | Decision | Trade-offs |
|---|---|---|
| Front end | Next.js + TypeScript on Vercel Hobby | Best demo ergonomics and type safety. Calls the API cross-origin, so the API enables CORS for the Vercel domain only |
| Back end | Python + FastAPI in Docker on Render Free | Pros: Python is the home of Pydantic, scikit-learn and AutoGluon, so demo and lab share one language; FastAPI derives OpenAPI from Pydantic for free. Cons: two runtimes and two deploy targets, a type-generation step, cold starts on the free host, 512 MB RAM. Alternative rejected: Next.js route handlers only, which would push the lab work into a second service anyway |
| Structured decisions | Jev via Vercel AI Gateway | See 2.2 |
| Validation | Pydantic v2 | Request/response models, the Jev question schema, the policy config, and the audit record are all Pydantic models |
| Contract | `openapi-typescript` from `/openapi.json` into `packages/contracts` | CI fails if committed types drift from the API. Hand-written shared JSON Schema rejected as double maintenance |
| Packaging | Docker | `docker compose up` runs API and web locally with hot reload; the API Dockerfile is what Render builds |
| Agent layer | Not in Phase 1 | Deferred to Phase 2 in full; see section 13 |

### 3.1 Contract pipeline

1. Pydantic models in `apps/api/app/schemas/`.
2. `make openapi` dumps `openapi.json` into `packages/contracts/`.
3. `npx openapi-typescript openapi.json -o packages/contracts/src/api.d.ts`.
4. CI runs steps 2 and 3 and fails on a dirty git tree.

### 3.2 Two-origin deployment

- `apps/web` deploys to Vercel from the repo; `NEXT_PUBLIC_API_URL` points at the Render service.
- `apps/api` deploys to Render from `apps/api/Dockerfile`; CORS allows the Vercel production and preview domains.
- Secrets: `JEV_API_KEY` (the AI Gateway key) lives only in Render's environment. Vercel holds no model keys in Phase 1.

---

## 4. Where each decision technique belongs

| Decision | Technique | Why |
|---|---|---|
| Customer tier: new / copper / bronze / silver / gold, by last visit spend in ₹ (see 4.1) | Deterministic rule | Exact numeric thresholds the owner specified directly. Auditable and always correct; running this through a model would add cost and uncertainty for no benefit — the textbook case for a rule, not AI |
| Branch opening hours | Deterministic rule (fact) | 10:00–20:00 for all three branches in Phase 1 seed data |
| Intent of an incoming message (book_appointment, reschedule, cancel, price_enquiry, complaint, feedback, other) | Jev `choice` | Free-text judgement needing probabilities; the only Jev output Phase 1's policy actually consumes |
| Service category requested (hair, skin, spa_body, nails, grooming, bridal, unclear) | Jev `choice` | Free-text judgement; shown and audited, not consumed by policy in Phase 1 |
| Urgency (4 levels) and frustration (3 levels) | Jev `score` | Ordinal judgement; shown and audited, not consumed by policy in Phase 1 |
| Asks for a specific stylist; asks for a callback | Jev `noul` | Cheap speculative questions; shown and audited, not consumed by policy in Phase 1 |
| Churn risk from visit history (tabular) | Conventional ML (logistic regression; Mitra-v2 zero-shot as comparator) | Labelled numeric history is what tabular ML is for; Jev on the same rows is the counter-experiment. Lab only, does not touch the deployed app |
| Final routing for a `book_appointment` message | Code: one rule — confirm if within branch hours, else auto-reject | See 4.2. Deliberately not confidence-gated in Phase 1 |
| Every other intent | Code: recorded only, no task, no rejection | Jev's full answer set is still saved to the audit trail; there is nothing to accept or reject about a complaint or a price enquiry in Phase 1 |

Removed from Phase 1 as of 2026-09-30: the `mentions_medical` question (did not map to a salon context), confidence-gated routing bands, and the "escalated case → Strands agent" row (nothing escalates in Phase 1; see section 13 for the Phase 2 version of this idea).

### 4.1 Tier rule, exact bands

| Tier | Condition |
|---|---|
| `new` | No customer record found in the seed data, **or** a record exists but has no completed visits yet |
| `copper` | Last visit spend < ₹1,500 |
| `bronze` | ₹1,501 – ₹3,000 |
| `silver` | ₹3,001 – ₹5,000 |
| `gold` | ₹5,001 and above (open-ended) |

Two adjustments to the owner's original wording, both flagged and accepted before implementation: the gold band is open-ended rather than capped at ₹10,000 (otherwise a bigger spender falls into no tier at all), and "record exists but zero visits" is treated the same as "record not found" under `new` (a registered customer who hasn't spent anything yet has no last spend to bucket either). "Last spend" is the most recent single visit's amount, not a 12-month total. There is no separate lifecycle field in Phase 1 — tier's `new` value covers that case, and the active/lapsed distinction by visit recency is deferred (see section 13).

### 4.2 Policy rule, exact logic

```python
def route(intent: str, branch: Branch, received_at: datetime) -> Decision:
    if intent != "book_appointment":
        return Decision(action="recorded", task=None)
    if is_open(branch, received_at):
        return Decision(action="confirmed", task=Task(type="booking_request", status="confirmed"))
    return Decision(action="rejected_outside_hours", task=None)
```

`is_open` checks the interaction's arrival time against `branch.openingHours` (data-driven, currently 10:00–20:00 for every branch, matching the owner's 10AM–8PM rule). "Booking time" is the time the interaction arrives, not a customer-requested slot — Phase 1 has no calendar or slot concept. Only three outcomes exist: `confirmed` (task created), `rejected_outside_hours` (no task), `recorded` (no task, applies to every non-booking intent). No thresholds, no priority formula, no medical gate.

---

## 5. Architecture (Phase 1)

```
Browser ── Next.js on Vercel ──(HTTPS, CORS)──▶ FastAPI on Render (Docker)

FastAPI (apps/api)
  POST /api/classify        state builder → JevClient → policy → Decision (+ Task if confirmed)
  GET  /api/customers       seed data (JSON fixtures)
  GET  /api/tasks           confirmed-booking board
  GET  /api/health          mode: live | replay; route: vercel-gateway | typesafe; budget remaining
  /openapi.json             source of the TS contract

  app/jev/       client.py (httpx), questions.py (Pydantic, 6 questions), replay.py (fixtures)
  app/rules/     tiers.py (5-band ₹ rule), hours.py (is_open)
  app/policy/    route.py — the single rule in 4.2
  app/audit/     SQLite file (ephemeral on Render Free; JSON export endpoint for the eval)

packages/contracts   openapi.json + generated api.d.ts
apps/web             message picker, decision panel (answers + confidence), task board, API-waking banner
lab/                 synthetic customers, logistic regression, Mitra-v2 (stretch), Jev eval runner
```

Cost and abuse controls before the URL is shared: per-IP rate limit on classify, daily Jev budget counter in the API plus a budget cap on the AI Gateway key, replay mode with recorded fixtures when the key is missing or the budget is exhausted, and a visible mode badge in the UI.

Privacy: the Jev `state` carries the customer id, tier, last three visits, the message text and branch context. Never names or phone numbers.

Persistence note: Render Free disks are ephemeral, so the audit store resets on each deploy or wake. Phase 1 accepts this and exports decisions to JSON for the eval; Phase 2 adds a hosted Postgres.

---

## 6. Data model (Phase 1 subset)

- Branch: id, name (fictional: Lakeview, Tech Park, Old Town), city, openingHours (10:00–20:00)
- ServiceCategory: hair, skin, spa_body, nails, grooming, bridal
- Service: id, categoryId, name, durationMin, priceBand
- Customer: id, displayName, phoneMasked, branchId, joinedOn, tier (new | copper | bronze | silver | gold, computed by the rule in 4.1, not stored redundantly if derivable from visits)
- Visit: id, customerId, serviceId, stylistId, date, spend (₹), noShow
- Interaction: id, customerId, channel (phone_note | web_form | whatsapp_mock), text, receivedAt
- Decision: id, interactionId, questionsSnapshot, answers, confidenceMap, policyVersion, action (confirmed | rejected_outside_hours | recorded), latencyMs, inputTokens, mode (live | replay), route
- Task: id, decisionId, type (booking_request — the only value in Phase 1), branchId, status (confirmed — the only value in Phase 1)

Removed from v2: the separate `lifecycle` concept (folded into tier), `priority` on Task (no queue to sort in Phase 1), and `EscalationNote` (no escalation in Phase 1; see section 13).

---

## 7. Evaluation plan

1. Golden set: 120 synthetic salon messages hand-labelled for intent, category, urgency, frustration and the two noul flags, including deliberately ambiguous ones. `eval/golden.jsonl`.
2. Per question: accuracy, macro-F1, mean confidence on correct vs incorrect answers, reliability plot (confidence bucket vs observed accuracy). This is an observational study of Jev's calibration — Phase 1's policy does not act on confidence, but the whitepaper's point is to show whether it *could* be trusted to.
3. Cost and latency: p50/p95 and tokens per call from `usage`, measured through the gateway.
4. Tabular churn: logistic regression vs Mitra-v2 zero-shot vs Jev given the same row as text. (Tier itself is not run through this comparison — it stays out of scope for Jev per the owner's decision in section 4.)
5. Self-consistency: three runs of the golden set; report flip rate.
6. Policy correctness: for every `book_appointment` message in the golden set, confirm the rule's outcome matches the branch-hours arithmetic exactly (this is deterministic code, so this is a regression check, not a model evaluation).

`make eval` runs 1 to 6 and writes `eval/results.json` plus a Markdown table. CI runs it in replay mode.

---

## 8. Milestones (4 weeks part-time)

| Week | Milestone | Done when |
|---|---|---|
| 0 | M0 Foundations | Vercel account, AI Gateway key, credits purchased, budget cap set; Jev answers a one-line Python call through the gateway; repo created with monorepo layout, licence, CI skeleton; `docker compose up` serves hello pages; ADR-0001 stack, ADR-0002 Jev access route, ADR-0003 hosting |
| 1 | M1 Jev spike + domain seed + contract | `questions.py` with all 6 questions as Pydantic models; CLI classifies one message and prints answers, probabilities, confidence; confidence presence through the gateway confirmed or computed; tier rule and is_open unit-tested; seed data (3 branches, 6 categories, 25 customers, 150 visits, 40 interactions); contract pipeline green in CI |
| 2 | M2 Workflow + demo UI | classify endpoint with the single policy rule and audit; UI with message picker, decision panel (answers, probabilities, confidence), task board, API-waking banner; replay mode and rate limit; API on Render, web on Vercel, CORS working |
| 3 | M3 Evaluation + lab | Golden set; `make eval` output; logistic regression done; Mitra-v2 attempted (stretch) |
| 4 | M4 Documentation + showcase | Whitepaper, ARCHITECTURE.md, WORKFLOW.md, README with GIF, LINKEDIN.md, `docs/PHASE2_ARCHITECTURE.md`; tag `v1.0.0` |

---

## 9. Learning plan (in order)

1. TypeSafe docs: introduction, quickstart, primitives, confidence, the four patterns. One paragraph per pattern in your own words into `docs/learning-notes.md`.
2. Vercel docs: the TypeSafe-compatible API page and the evaluation modality page. Note the two response dialects and why we use the TypeSafe one.
3. Exercise: write the 6 questions, then rewrite each criterion once to be more specific and measure the change on 10 golden messages. Criteria wording is Jev's prompt engineering.
4. Exercise: compute confidence for a batch of messages and look at the reliability plot before deciding whether you'd trust it to gate anything in a later phase.
5. FastAPI + Pydantic v2: models, dependency injection for the JevClient, settings from env. Then `openapi-typescript`.
6. Python lab: scikit-learn logistic regression; AutoGluon Mitra-v2 zero-shot; record install and run time honestly.
7. Write the whitepaper section "What surprised me" last.

---

## 10. Repository layout

```
abc-salon/
  README.md  LICENSE  Makefile  docker-compose.yml
  .github/workflows/ci.yml          lint, test, contract check, eval (replay)
  apps/api/                         FastAPI (Dockerfile, app/, tests/, pyproject.toml)
  apps/web/                         Next.js (deployed by Vercel)
  packages/contracts/               openapi.json, src/api.d.ts
  data/seed/                        branches, services, customers, visits, interactions (JSON)
  eval/                             golden.jsonl, results.json, README.md
  lab/                              notebooks and scripts, own requirements.txt
  docs/                             PHASE1_PLAN.md, ARCHITECTURE.md, WORKFLOW.md, WHITEPAPER.md,
                                    LINKEDIN.md, PHASE2_ARCHITECTURE.md, learning-notes.md, adr/
```

No `app/agent/` directory in Phase 1; it is introduced in Phase 2 if the owner confirms the proposal in section 13.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Jev is days old; access routes, SDKs and pricing are moving | `JevClient` interface, env-driven base URL, recorded fixtures, pinned versions |
| Gateway response may lack `confidence` | Compute from probabilities with TypeSafe's definition; document it |
| Gateway spend from a public demo | Server-side key, rate limit, daily budget in code, budget cap on the gateway key, replay mode |
| Render cold start hurts first impression | UI banner and health poll; README notes the wake time; optional uptime pinger is not used because it burns free hours |
| 512 MB RAM on Render Free | No ML libraries in the API image; lab stays offline |
| Ephemeral disk on Render Free | Audit store is a cache; eval reads exported JSON |
| Synthetic data makes accuracy claims meaningless | Say so in every document; present results as behaviour on a controlled set |
| Mitra install on Windows | WSL2 or Colab; stretch goal |
| Two runtimes raise setup cost for reviewers | `docker compose up` is the only documented way to run it |
| Copying the reference salon | Fictional names, generic categories, no images or copy |
| Scope creep into booking | Phase 1 creates Tasks, never Appointments |
| A reviewer expects Jev to explain the tier decision | Whitepaper states explicitly, with the exact rule, why tier is deterministic code and not a model call |

---

## 12. Definition of done for Phase 1

- Public URL works with no API key (replay mode) and with a key (live mode), and the UI shows which mode is active.
- `make test`, `make contract-check` and `make eval` pass in CI.
- Whitepaper contains the technique-comparison table with measured numbers and the reliability plot, and explains why tier and the hours check are rules rather than Jev calls.
- ARCHITECTURE.md and WORKFLOW.md diagrams render on GitHub.
- LINKEDIN.md has a post you would actually publish.
- `docs/PHASE2_ARCHITECTURE.md` exists with the receptionist booking flow, mock WhatsApp adapter interface, the confidence-gated escalation proposal, and a learning list. No Phase 2 code.

---

## 13. Deferred to Phase 2: escalation and the Strands agent

Per the owner's "hold on Phase 2" instruction of 2026-09-30, none of this is built in Phase 1, including the Strands lab walkthrough. It is recorded here so it is not lost, and so `docs/PHASE2_ARCHITECTURE.md` (M4 deliverable) has a starting point:

1. **Confidence-gated escalation.** Reintroduce bands on Jev's `intent` confidence (or another answer) so a genuinely ambiguous message routes to a human queue instead of just being recorded. This is the natural home for the reliability-plot work already being done in the Phase 1 evaluation (section 7.2) — Phase 2 decides whether to act on confidence, having first measured in Phase 1 whether it is trustworthy.
2. **A medical or safety check**, redesigned to actually fit a salon (allergy to a hair or skin product, a treatment unsuitable during pregnancy) rather than the generic wording that prompted its removal from Phase 1.
3. **Manager Assistant.** A Strands agent (`strands-agents` SDK, Anthropic model, custom tools only — `lookup_customer`, `ask_jev`, `propose_task`; never the harness's default shell/file/web tools) that drafts a proposal on an escalated task for a human to approve. This only makes sense once item 1 exists to produce escalated tasks for it to act on.
4. Stylist and slot availability checks, replacing the flat branch-hours check with real capacity.
5. Tier-based priority queueing (gold customers get faster handling).
6. Reintroducing an active/lapsed signal by visit recency, separate from spend-based tier, if churn timing turns out to matter.

---

Sources checked:
- https://docs.typesafe.ai/introduction, /introduction/quickstart, /primitives, /confidence, /patterns, /patterns/intent-routing.md, /api.md, /sdk/javascript.md, /sdk/python.md
- https://pypi.org/project/typesafe-sdk/
- https://typesafe.ai/blog/introducing-system-one-models-and-jev
- https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe, /docs/ai-gateway/modalities/evaluation, /docs/ai-gateway/pricing, /ai-gateway/models?freeTier=true, /changelog/ai-gateway-now-supports-typesafe-clients-and-http-api-for-jev, /kb/guide/typesafe-jev-and-ai-sdk
- https://developers.cloudflare.com/ai/models/typesafe/jev/, /workers-ai/platform/pricing/
- https://github.com/strands-agents/harness-sdk, https://strandsagents.com/docs/user-guide/harness/, https://pypi.org/project/strands-harness/
- https://huggingface.co/autogluon/mitra-classifier-2, https://auto.gluon.ai/stable/tutorials/tabular/tabular-foundational-models.html
- https://huggingface.co/docs/hub/en/spaces-overview, /docs/hub/spaces-sdks-docker, https://huggingface.co/pricing
- https://render.com/docs/free, https://render.com/docs/docker
- https://docs.fly.io/about/pricing/
- https://docs.cloud.google.com/free/docs/free-cloud-features
- https://www.eleggancespa.com/ (structure only)
