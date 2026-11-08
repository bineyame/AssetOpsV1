# Review: OWN-G3a, saving operational records from the screen (backend)

Reviewer: fresh Claude (Opus) reviewer, independent of the builder. Branch `task/OWN-G3a-operational-entry-api`,
head reviewed `834a7fb22` (packet commit; product code unchanged since `b1cd17701`). Diff: `git diff
main...task/OWN-G3a-operational-entry-api` (base `1d666d410`). Spec: `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`
§1, §3.1, §3.2, §3.4-§3.6 (G3a), Revision 1, Revision 2 R2-G3a 1-6.

## Verdict

**ACCEPT WITH NOTES.** No High or Medium findings. Three Low notes, none blocking.

## What was checked against the spec

| Item | Result |
|---|---|
| Route `POST /api/sites/{site_code}/work/operational-entries`, new keywords `entry_principal`, `site_context` | Present, `work_api.py:198-216`, `:110-111`. |
| Refusal order (R2-G3a 1): access/404/write grant, then principal 403, then 503 (`service` or `site_context` None), then shape 422, then tank/zone, then service | `gate.open_scope(request, site_code, True)` (grant checked, store not), `who is None` 403, store 503, then `validate_entry` before `site_context` inside `run`. Matches. Tests pin each step, including 403 with an invalid body and no store, and 503 before shape. |
| The W4 `principal` is not used for this route; the existing `/operational-records` route is unchanged | Confirmed; `test_the_existing_record_route_keeps_its_own_principal`. |
| Closed body, five required keys, null ticket allowed (R2-G3a 4) | `set(body) != set(ENTRY_KEYS)` (`operational_entry.py:53`); an `actor` key or any extra key is 422 `OPREC_ENTRY_INVALID`. |
| Validation order and patterns (§3.2 steps 1-5) | Uses `fullmatch` with `[0-9]` (stricter than the spec's `\d`, which in Python also matches non-ASCII digits; no `$`-before-newline hole). Delivery > 0, `strptime` rejects invalid dates/hours, ticket required only for delivery (null → `OPREC_ENTRY_TICKET_REQUIRED`, `""`/miss → INVALID), non-fuel ticket must be null, key pattern. Type checks reject bools/numbers. |
| Normalisation (R2-G3a 3) | `m.decimal_text(Decimal(raw))` feeds body, digest text and quantity; `198`/`198.0`/`0198` identical, `198.50` → `198.5` (unit and Postgres). `0`/`000` → `0`; `100` → `100` (no exponent). |
| Mapping table, K7 literals, digest | Matches §3.2 exactly; digest over ASCII text, safe because the ticket pattern is ASCII-only. Manual readings carry no `asset_id` key. |
| Time zone (fold 0, UTC wire) | `occurred_utc`; Dar 06:00 → 03:00Z tested. `site.timezone` is `NOT NULL` (`migrations/versions/0001_foundation_identity.py:67`), so `night_context`'s `str | None` zone cannot reach `ZoneInfo(None)` for a scoped Site. |
| Actor, attestation (Rev 1 `job=site-admin-entry`), principal `service:operator-entry` | Constants in `operational_entry.py:25-27`; stored columns proven on Postgres including `authorization_basis = SITE_WORK_WRITE:service:operator-entry`. |
| Codes and literals (R2-G3a 5, §3.2) | `work/model.py` MESSAGES and STATUS (422 each), exact text. |
| Site context from the one fuel store (R2-G3a 2) | `main.py` builds one `fuel_store`, shares it with `FuelNightRead` (dispose kept) and `entry_site_context(fuel_store.night_context)`; both `None` without a URL, so the route is 503 then. |
| Env gate (R2-G3a 6) | `host/lab_app.py:77-97`: unset/empty → off, `on` → principal, anything else (`yes`, `ON`, `on `) → `ConfigurationError` before anything is built; `setdefault` keeps an explicit override. The only non-default injection site in product code is `lab_app.build_app`; `main.app` and every other `create_app` caller default to `no_service_principal` (403). No write is possible with the gate off. |
| Demo serve env | `tools/demo_combined.py` `serve_env` adds `ASSETOPS_OPERATIONAL_ENTRY=on`; tick children share it (CH5c-R6 parity kept). |
| Idempotency and duplicates | Delegated to `WorkService.post_operational_record`: identical retry → 200 stored body, same key different value → 409 `WORK_EVENT_DUPLICATE_KEY`, zero extra rows (Postgres). The retry check precedes the 30-day check, so a late retry of a saved entry still returns 200. |
| Audit trail | Existing `operational_record` row; REC code, actor, attestation, basis, `payload_sha256`, key and `recorded_at` within DB `clock_timestamp()` bounds asserted on Postgres. |
| Feeds the fuel balance | `build_fuel_records_reader` returns the saved dip for its window (Postgres). |

## Deviations

- **D1 (broad 503 mapping instead of naming `SQLAlchemyError`): acceptable.** `tools/checks/configuration-persistence.ps1:295`
  forbids `sqlalchemy`/`psycopg` imports outside the adapters, so the ruling's literal form would fail the architecture
  guard. The builder reuses the established `fuel_balance/night_read.py:59-66` `_guard` shape (re-raise `ValueError`,
  `TypeError`, `KeyError`, `AttributeError`; everything else → unavailable). It is a superset of the ruling: the
  driver errors and the no-URL `RuntimeError` both become 503. See L1 for the residual masking.
- **D2 (named `operational_entry_principal` instead of an inline lambda): acceptable.** Same return literal; allows
  the identity assertion in the env test.
- **D3 (public `validate_entry`, called before the Site context): acceptable, and needed** to honour the R2-G3a 1 order
  (shape before tank and zone) while keeping `compose_entry(body, timezone, tank_id)` pure as §3.2 specifies. The
  double validation is cheap and deterministic.

## Findings

No High. No Medium.

- **L1 (Low, residual risk) `backend/assetops_backend/work/operational_entry.py:97-101`.** The catch-all maps any
  exception other than the four named programming errors (for example `IndexError`, `ZeroDivisionError`, `NameError`)
  from `night_context` to 503 `WORK_STORE_UNAVAILABLE`, which would hide a coding bug behind an "unavailable" message.
  Same trade-off as the existing `_guard`; the chained cause keeps the class name in the exception text. No change
  required for this slice; a shared adapter-side "store unavailable" exception would remove the guess later.
- **L2 (Low, test coverage) `host/tests/test_own_g3_entry_env.py:44-54`.** The env → `create_app` wiring is proven with
  a stubbed `create_app`, and the write path with a directly injected lambda in the Postgres test. No single test
  posts through a real `lab_app.build_app()` with the variable on. The two halves together cover the behaviour; G1's
  in-process `app_client` will exercise the joined path. Preference, not an acceptance gap.
- **L3 (Low, spec-conformant edge) `operational_entry.py:35`.** The ticket pattern (as specified) allows a trailing
  space, so `"KIS-1 "` stores "ticket KIS-1 ." and a different digest from `"KIS-1"`. The form (G3b) should trim
  before sending; noted for G3b, no G3a change.

## Checks run (by me, at `834a7fb22`)

- `backend/tests/test_own_g3_operational_entry.py` + `host/tests/test_own_g3_entry_env.py` +
  `backend/tests/test_w401_work_api.py` (no DB URL): **62 passed, 11 skipped** (the w401 Postgres cases), 4.8 s.
- `backend/tests/test_own_g3_operational_entry_postgres.py` on my own base `assetops_g3arev_test`
  (created for this review; 4.7 GB free RAM before): **8 passed, 0 skipped**, 27.6 s pytest, 31 s wall.
- Adjacent no-DB: `test_ch5c_store_off`, `test_ch5c_env_parity`, `test_k2_fuel_records`,
  `test_w601e_operational_index`, `test_health`: 38 passed, 12 skipped, **1 failed**
  (`test_ch5c_env_parity::test_the_tick_child_and_the_serve_child_compute_one_code_version`, `SystemExit: Run prepare
  first.`). I reproduced the same failure on main `1d666d410` in `AssetOpsV1-plan2`, so it is pre-existing and not
  caused by this slice.
- `tools/check-architecture.ps1`: ARCH_RESULT
- `tools/check-agent-workflow.ps1`: WF_RESULT
- Frontend checks: not applicable (no frontend files in the diff). Layout evidence: not applicable (backend slice).
- No full suites (per brief and the demo-sprint suite policy). The packet records none either.

## Residual risk not named in the packet

- The 30-day refusal sits after the idempotency lookup, which is correct, but G1 posting historic dates will meet it
  for new keys (already ruled in R2-G1; recorded here only for completeness).
- Any other launcher of `host.lab_app` outside `tools/demo_combined.py` (capture tools, ad-hoc `uvicorn`) starts with
  the route off unless it sets the variable. This is the intended fail-closed behaviour; G3b captures that need a
  save must set it.
