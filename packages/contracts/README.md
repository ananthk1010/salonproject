# @abc-salon/contracts

Generated, not hand-written. Do not edit `openapi.json` or `src/api.d.ts`
directly — regenerate them with `make contract` (or the two commands it
wraps) after changing any Pydantic schema in `apps/api/app/schemas`:

```bash
python apps/api/scripts/export_openapi.py
npx openapi-typescript packages/contracts/openapi.json -o packages/contracts/src/api.d.ts
```

CI runs the same two commands and fails the build if the committed files
differ from what they regenerate to — that is the drift check described in
docs/ABC-Salon_Architecture_Design.docx section 9.1.

`apps/web` currently uses hand-written types in `lib/types.ts` kept in
sync manually; wiring it to import `paths` from this package directly is a
natural follow-up once the schemas stop changing every few days.
