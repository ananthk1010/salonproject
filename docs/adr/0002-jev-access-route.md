# ADR-0002: Jev access via Vercel AI Gateway, not TypeSafe direct

Status: Accepted (2026-09-25)

## Context

TypeSafe AI's own console (console.typesafe.ai) returned
`signups_disabled` when the owner tried to register on 2026-09-25.
Third-party reports say direct signups were paused on 2026-09-22, shortly
after a brief open period; no reopening date is published. Phase 1 cannot
wait indefinitely for that to change.

Update, 2026-10-03: direct console access is open again, but the owner
reports that the $5 credit is offered only to organizations with a GST
registration, not to individual accounts. Direct access therefore gives
the owner no cost advantage, so the decision below stands unchanged.
Switching later, if TypeSafe extends credits to individuals, is a
configuration change only (`JEV_BASE_URL=https://api.typesafe.ai`,
`JEV_MODEL=jev-latest`, and a TypeSafe key in `JEV_API_KEY`).

## Decision

Call Jev through Vercel AI Gateway's TypeSafe-compatible endpoint:

- Base URL: `https://ai-gateway.vercel.sh/typesafe`
- Endpoint: `POST /v1/systemone` (TypeSafe's own request/response shape,
  not the gateway's native `/v1/evaluate` dialect, to keep the code
  portable to TypeSafe direct later)
- Auth: a Vercel AI Gateway API key, not a TypeSafe key
- Model id: `typesafe-ai/jev`

Implemented as a small (~100-line) `httpx`-based client
(`apps/api/app/jev/client.py`) rather than the official `typesafe-sdk`
Python package, because that SDK has no documented way to override its
base URL — it only talks to TypeSafe's own API.

The base URL, key, and model are all environment variables
(`JEV_BASE_URL`, `JEV_API_KEY`, `JEV_MODEL`), so switching to TypeSafe
direct, or to Cloudflare Workers AI's native `typesafe/jev` endpoint, is a
configuration change, not a code change.

## Consequences

- Jev is not in the gateway's free-tier model list, so AI Gateway Credits
  must be purchased; a budget cap on the key and a daily token budget in
  `app/audit/store.py` protect against runaway spend.
- Whether the gateway's response includes `confidence` for `choice` and
  `score` answers was unverified at design time. `app/jev/client.py`
  computes a fallback from the probability distribution if it's absent
  (`confidence_from_probabilities`, matching TypeSafe's published
  3-option formula generalised to n options) and flags every such answer
  with `confidence_is_fallback: true`.
