# G3a pre-flight: saving operational records from the screen (backend)

Branch `task/OWN-G3a-operational-entry-api` from main `59a89397a`. Spec: `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`
Revision 1, §1, §3.1, §3.2, §3.4 (G3a), §3.5 (G3a). Read-only; no Postgres run; no product code.

## Anchors checked (match unless noted)

- `main.py:603-609` no work principal injected: matches. `work_api.py` docstring: the 201/200 line is `:16` (spec `:15`), the
  Q28 client-actor line is `:22-24` (spec `:20-23`). `work/model.py:279-282` USER 403 / no principal 403: matches.
- `WorkService.post_operational_record` (`work/service.py:474-532`): closed keys `OPERATIONAL_KEYS` + optional
  `asset_id` (`:35-42`), actor via `m.authorize` (`model.py:276-287`: id must equal the principal and `service:`+attestation
  service), idempotent retry before `check_occurrence` (`:505-509`), `REC-` code, `SERVICE_GRANT_PREFIX + principal`
  basis, fuel rules `_fuel_asset` (`:534-552`). The spec's actor/attestation/principal satisfy `authorize`.
- `STATUS` / `MESSAGES` (`model.py:39-74`): `WORK_EVENT_DUPLICATE_KEY` is 409; the occurrence codes 422; quantity 422.
- K7 literals `tools/demo_combined_kisiwa.py:201-203`: match the spec table verbatim.
- `night_context` (`postgres_fuel_balance_store.py:236-246`) returns `(timezone, tank_id | None, read_instant)`; `site.timezone`
  is `NOT NULL` (`migrations/versions/0001_foundation_identity.py:67`).
- `build_fuel_records_reader` (`work/composition.py:44-48`) returns `select_fuel_records(c, tenant, site, tank, lo, hi, known_at)`
  (`work/adapters/postgres_fuel_records.py:40`); the Postgres test can call it on a connection.
- `host/lab_app.py:67-95` `build_app`; `ConfigurationError` is `assetops_backend/config.py:27`. Serve runs `lab_app:app`
  with `serve_env()` (`tools/demo_combined.py:357-361, 820-821`); the tick children use the same env, and
  `test_ch5c_env_parity.py` keeps them equal, so setting the variable in `serve_env()` keeps parity. The variable is not in
  `chain/watermark.py` `COMPOSER_ENV`, so it does not change `code_version`.
- Guards: no `tools/checks` rule names `work_api`, the principal seams or `lab_app` env reads; no new table writer
  (rule 8 untouched). `test_health.py` pins `{site_id}` paths only; the new path uses `{site_code}`.
- Postgres fixture: `test_k2_fuel_records_postgres.py` imports Kobo (one `FUEL_TANK`) via `test_s1_bindings_postgres.imported`;
  reusable for "fixture Site with one tank".

## Questions (one batch)

**Q1. The write grant in the refusal order.** §3.2 "Refusal order" lists read access/404, then principal 403, then store 503.
The shared `WorkGate.open_scope` (`work_api.py:88-97`) also applies the write grant `command_access` 401/403 after 404 and
checks store availability *before* returning the principal (the service then checks the principal, `service.py:124-126`),
so reusing it unchanged with `available=service is not None` would answer 503 before the principal 403, contrary to
§3.2's order (principal 2, store 3). **Proposed:** call `gate.open_scope(request, code, True)` (read
access, 404, write grant 401/403 — `development_access` in `main.py`, so no behaviour change), then entry principal absent
-> 403 `WORK_WRITE_FORBIDDEN`, then 503 when `service is None` or `site_context is None`, then shape. Confirm the grant step
stays in.

**Q2. `site_context` default and composition in `main.py`.** §3.2 gives no default and no failure mapping. `night_context`
raises SQLAlchemy errors (or `RuntimeError` with no URL, `postgres_fuel_balance_store.py:182-184`); the router's `run`
catches only `WorkStoreUnavailable` (`work/composition.py:33`), so an outage would be a 500. `main.py:559` already builds a
fuel-balance store for `FuelNightRead`. **Proposed:** keyword default `site_context=None` (-> 503 after the principal check);
in `main.py` build one store `fuel_store = build_fuel_balance_store(database_url())`, pass it to `FuelNightRead` as today
(it keeps disposal) and compose `site_context` from `fuel_store.night_context`, dropping the instant and mapping
`SQLAlchemyError` to `WorkStoreUnavailable` (503 `WORK_STORE_UNAVAILABLE`). Alternative: a second store instance with its
own shutdown dispose (one more engine pair).

**Q3. `{value}` in the body and ticket digest: as typed or normalised?** The regex admits `198.50`, `0198`, `198.0`. The
service stores `quantity` normalised (`m.decimal_text`, `model.py:220-225`), so a typed `198.50` would store quantity `198.5`
with body "... 198.50 L", and `198` vs `198.0` with one key would be a 409 duplicate. K7 writes integers (`str(int)`).
**Proposed:** use `m.decimal_text(Decimal(value))` for `{value}` in the body, the ticket text and `quantity`, so body,
digest and quantity agree and match K7's form for whole litres.

**Q4. Required keys and the empty ticket.** "A closed object (any other key -> 422)" does not say whether all five keys
must be present. **Proposed:** all five required (`ticket_reference` present, null allowed); a missing key -> 422
`OPREC_ENTRY_INVALID`; for `FUEL_DELIVERY`, `null` -> `OPREC_ENTRY_TICKET_REQUIRED`, `""` or a pattern miss -> `OPREC_ENTRY_INVALID`
(literal reading of "required (non-null)"); validation stops at the first failing step, so a delivery with value `0`
and no ticket is `OPREC_ENTRY_INVALID` (step 2 before step 4).

**Q5. Messages for two new codes.** §3.2 gives only `OPREC_ENTRY_NO_TANK`'s message. **Proposed** `MESSAGES` literals:
`OPREC_ENTRY_INVALID`: "The entry, value, time taken, ticket reference or key is not valid."; `OPREC_ENTRY_TICKET_REQUIRED`:
"A fuel delivery needs its ticket reference."

**Q6. Where the startup-refusal test lives, and override precedence.** §3.5 puts "`ASSETOPS_OPERATIONAL_ENTRY=yes` refuses
startup" in `backend/tests/test_own_g3_operational_entry.py`, but no backend test imports `host/lab_app.py` (only a
source-text read, `test_ch0_tick_timing.py:230-231`); importing it runs `app = build_app()` at module level
(`lab_app.py:95`) with the kernel imports. **Proposed:** a small helper in `lab_app.py`
(`OPERATIONAL_ENTRY_ENV = "ASSETOPS_OPERATIONAL_ENTRY"`, `operational_entry_from_environment() -> Principal | None`, raising
`ConfigurationError` for any other non-empty value), called by `build_app` before `create_app`, setting
`overrides.setdefault("operational_entry_principal", ...)` only when on (an explicit test override wins); its tests
(`on`, unset, empty, `yes`) in a new `host/tests/test_own_g3_entry_env.py`. If the backend file must hold it, it would
add `host/` to `sys.path` and call the helper only (never import-time `app`).

**Q7 (FYI for G1, no G3a change proposed).** Rev 1 §3.1 says G1 posts Kisiwa dips and deliveries through this route.
Through HTTP the service uses the real DB clock: entries more than 30 days back are refused (`model.py:245-249`), and a
back-filled delivery is recorded "now", so it would carry `DELIVERY_RECORDED_LATE` (K3 §9d.3); K7 today posts with a
virtual DB clock and `recorded_after_minutes` offsets (`demo_combined_kisiwa.py:400-411, 434-441`). G1's "any date up to
yesterday" therefore meets these limits; the G1 card should rule on them.

**Q8 (FYI for G3b).** The global list's `record_kind` filter (`work/operational_index.py:26`) offers no `TANK_DIP` or
`FUEL_DELIVERY`; under `all` they are listed. No G3a change proposed.

Count: 6 questions needing a ruling (Q1-Q6), 2 FYI notes (Q7-Q8).
