# PR-3 packet: site-admin price entry, server half

Branch `task/PR-3-price-entry` (worktree `AssetOpsV1-pr3`), from main `34465972b` + `task/PR-1-price-action` `24e6728d4`
merged. Spec: `.agent/architect-sequence-client-scope-2026-11-11.md` revision 5 §5.3; D-PRICE.1
(`build-sheet-OWN-GAPS-2026-11-08.md:4323`); owner defaults approved (`owner-price-entry-defaults-2026-11-12.md`).
Scope of this half: server, migration, no-DB tests, one Postgres flow file. **No UI** (form is Friday, on PR-2a).

## What is built

| Piece | Where |
|---|---|
| `SITE_ADMIN_CHANNEL`, `SYSTEM_CHANNELS` widened, `SITE_ADMIN_PRICE_PUBLISHER` (actor = imported `ENTRY_PRINCIPAL`), `SITE_ADMIN_PROVENANCE` | `backend/assetops_backend/financials/assumptions.py:57-62, 77-83` |
| Pure entry logic: closed shape (step 6, every failing field in `fields`), future key (step 7), derivation (step 9), summaries, `set_by` | `backend/assetops_backend/financials/price_entry.py` (new) |
| Route `POST /api/sites/{code}/financial-assumptions/entries`, refusal order 1-10, dry run, save 201/200 | `backend/assetops_backend/financial_api.py` `build_financial_assumption_router` |
| Composition: same `operational_entry_principal` switch, `build_assumption_store`, Site zone via `entry_site_context(fuel_store.night_context)`, `read_access=development_access` | `backend/assetops_backend/main.py` (financial router include, ~l.648) |
| Migration `0060_site_admin_price_entry` (down_revision `0059_site_period_read`): channel CHECK widened, guarded on `financial_assumption_revision_channel_check`; downgrade refuses while a `SITE_ADMIN_ENTRY` row exists | `backend/migrations/versions/0060_site_admin_price_entry.py` |

The human route `POST /financial-assumptions` is untouched (still 401 `UNAUTHENTICATED` / `HUMAN_PRINCIPAL_REQUIRED`).
No recompute runs inline; the outbox trigger and 0011/0026 queueing do it (rev 5 §5.1).

## Refusal table as tested (`test_pr3_price_entry.py::TestRefusalOrder`)

Each case fails every later step too, so the order is pinned.

| # | Status / code | Test |
|---|---|---|
| 1 | 404 (scope None), before access | `test_1_unknown_site_404_before_access` |
| 2 | 403 `SITE_SCOPE_FORBIDDEN` (read access) | `test_2_read_access_403` |
| 3 | 403 `PRICE_ENTRY_OFF` "Saving prices is switched off on this server." | `test_3_entry_off_403` |
| 4 | 422 `BODY_NOT_JSON` | `test_4_body_not_json` |
| 5 | 422 `CLIENT_ACTOR_FORBIDDEN` (+`fields`) | `test_5_client_actor_before_shape` |
| 6 | 422 `PRICE_ENTRY_INVALID` (+`fields`) | `test_6_shape_before_store`, `TestShape` (27 bad values, 7 missing, closed object) |
| 7 | 422 `PRICE_KEY_NOT_ENTERABLE` | `test_7_future_key_before_store`, all 4 future keys |
| 8 | 503 `ASSUMPTION_STORE_UNAVAILABLE` (no store; store/zone failure; scope outage) | `test_8_*`, `test_scope_outage_is_503` |
| 9 | 422 `APPLIES_FROM_OUT_OF_RANGE` → `CURRENCY_DIFFERS` → `REASON_REQUIRED` | `test_9_*`, `test_bounds_are_inclusive` |
| 10 | store `PublicationRefused` unchanged (plan 409, `IDEMPOTENCY_KEY_REUSED`) | `test_10_*` |

## Derivation table as tested (`TestDerivation`, Site zone Africa/Nairobi, now 2026-11-12 10:00Z)

| Series | applies_from | change_kind |
|---|---|---|
| none | past / tomorrow | INITIAL |
| bounded price ending before the date | past | INITIAL (no overlap) |
| open price | tomorrow | SUCCESSION |
| open price | today / past | CORRECTION (reason required) |

`valid_from` = Site-local midnight as UTC (10 Nov Nairobi → 2026-11-09T21:00Z); Site "today" is local (22:30Z on
12 Nov is 13 Nov in Nairobi). `expected_prior_revision_id` = series head (highest `revision_no` cited by a current
assignment; the head's own assignment is always current). A reason with INITIAL/SUCCESSION → `provenance.entry_note`.

## Postgres flow (`test_pr3_price_entry_postgres.py`)

Command (own DB, base `assetops_pr3_test`; PYTHONPATH = worktree `contracts;backend;backend\tests;simulator;tools;
host;gateway;field`): `python -m pytest backend\tests\test_pr3_price_entry_postgres.py -q -s --junitxml=...`.
Revision `51da89871` (after merging main `946a02661` and PR-1 `b4f8e8876`): **2 passed, 0 failed, 0 skipped**
(JUnit tests=2), wall 42 s. Same result on `571d3e101` before the merge.

- `test_0060_widens_the_channel_check_and_downgrades_cleanly`: single head 0060 → 0059; installed CHECK text; empty
  downgrade restores the 0010 text exactly; upgrade back.
- `test_a_saved_price_reaches_the_fuel_cost_after_one_drain` (PowerSite, v1 = 1.25 USD from 2026-01-01):
  - dry run → 200 CORRECTION, `reason_required` true, no row written;
  - save (CORRECTION from 1 Oct, 2.00 USD, reason) → 201, revision 2, `set_by` "Entered by site admin";
  - row: channel `SITE_ADMIN_ENTRY`, actor_kind `SYSTEM`, actor `service:operator-entry`, `author_id` NULL,
    `correction_reason` kept, provenance `{service, job: site-admin-price-entry, rule: price-entry/1}`;
  - one `price.revised` outbox row (subject key `diesel_price_per_litre`);
  - replay with same key and body → 200 `replayed: true`, still 2 revisions;
  - fuel cost before the drain: STALE, `pending_work` present, not presented as current;
  - **fuel cost: before 3.4375 → after one `run_pending` drain 5.5000** (2.75 L × 2.00), price revision = saved one;
    the old consequence revision still reads 3.4375 (historical);
  - **window price as known before the save 1.25, current 2.00** (`store.snapshot(recorded_at=...)`);
  - downgrade with a site-admin row refused ("Downgrade of 0060_site_admin_price_entry refused"), head unchanged.

First run found a real defect: a retry after a save re-derived against the new head (prior = itself), so the digest
differed and it would have been 409, not a replay. Fixed in `571d3e101` (`price_entry.derive`: when the head carries
this idempotency key, re-derive that save's kind and prior; unit test `test_a_retry_of_the_head_save_rederives_that_save`).

## Checks

- No-DB: `test_pr3_price_entry.py` **84 passed**. Adjacent (s4 publication/read API, PR-1, any1 period read, ch5c
  store-off, OWN-G3 entry, AR-3/AR-6 no-DB) with PR-3: 283 passed after the main merge (332 passed, 6 skipped on the
  wider pre-merge set incl. consequence history, s5 overview, w204 cold reads).
- `tools\check-all.ps1 -Python <plan2 venv>` on `571d3e101`: 17/19 PASS (wall 36 min, the estate guard alone 29 min
  under machine load); the 2 missing-claim guards failed with `MODULE_NOT_FOUND typescript` (fresh worktree has no
  `frontend/node_modules`). After a junction to main's `node_modules`: missing-claim scan passed, fixtures 26/26.
  **19/19.** Not rerun on the merge commit (no PR-3 file changed by the merge).
- Full backend suite: not run (demo-sprint policy; one Postgres file only).
- Layout evidence: not applicable (no UI in this half).

## Known deviations / interpretations (each small; Architect to confirm)

1. **Dry run does not refuse `REASON_REQUIRED`.** Rev 5 says the dry run "runs steps 1-9", but the UI shows the
   Reason field when the dry run says `reason_required`, which a refusal could never return. The dry run returns 200
   with `reason_required: true`; the save refuses 422 `REASON_REQUIRED` without a reason.
2. **`read_access` default is `no_verified_principal`, not the development access.** `test_s4_assumption_publication`
   guards that `financial_api.py` never names `development_access`/`finding_api`; main.py injects
   `development_access` explicitly (same effective behaviour, guard not loosened).
3. **Two extra router keywords:** `unavailable` (store/zone/scope failures → 503) and `clock` (server now, injectable
   for the change-kind tests). A scope outage is 503 rather than a 500 (Site scope raises without a database).
4. **`{Site}` in the INITIAL summary is the Site code** (`KOBO-001`); the scope gives no Site name. See Q1.
5. **Postgres "money line"**: the flow proves the S4 Finding fuel-cost consequence (the 0011 queue + recompute
   worker drain) and the window price "as known before the save" via `store.snapshot(recorded_at=...)`, not the
   AR-4 `money.lines` read (not on main). Rerun when AR-4 lands (rev 5 contract line).
6. **Not built here (belong to PR-2a / form half):** `entry: {enabled, keys}` on the PR-2a page read and its
   `known_at` test; the `actor_id → set_by_label` History map; the AR-4 register line. Postgres items not covered in
   this file: productive-use INITIAL making the mill value priced and its `price_action` disappearing; "stored
   Financials response not served after a save". Both listed as resume points.

## Fix round (review L1, L2, D-PRICE.2 #4), 2026-11-12

- **L1** `price_entry.derive` finds the idempotency key anywhere in the series (`_series_revisions`; the route reads
  `SERIES_LIMIT = 1000` revisions), so a retry after a later save replays (200). Tests: no-DB
  `test_a_retry_replays_when_another_save_followed_it`; Postgres flow extended (second save on another key, then
  the retry of the first returns 200, same revision id, 3 revisions).
- **D-PRICE.2 #4** new router keyword `site_name(tenant, site)`, composed in `main.py` as
  `PostgresAssumptionStore.site_name` (`site.name`, the column the estate Financials read serves as `site_name`);
  null name falls back to the code; a failed lookup is 503 `ASSUMPTION_STORE_UNAVAILABLE`. Tests: name, null
  fallback, failure 503. Q1 and Q2 are answered by D-PRICE.2 (deviation 4 resolved).
- **L2** two Postgres tests added to `test_pr3_price_entry_postgres.py`: (a) mill (productive-use) value UNPRICED with a
  SET_PRICE `price_action`, then an INITIAL price saved through the route, then the verdict reads PRICED 17.00 with
  no `price_action`; (b) the response watermark (`chain_input_change`) moves after a save, a body stored under the
  old watermark is not found under the new one (non-vacuous: found under the old), and the fresh price read lists
  the saved revision.
- Results: no-DB `test_pr3_price_entry.py` 88 passed; Postgres file 4 passed, 0 skipped (41 s, main merged first).

## Form half (2026-11-12, after merging main `adf869b08`, which carries PR-2a)

Merge was clean; migration head stays single (`0060_site_admin_price_entry` → `0059_site_period_read`).

| Piece | Where |
|---|---|
| `entry` block + entry-on sign-in sentence (default 7) on the PR-2a page read | `financials/price_page.py` `entry_block`, `compose(entry_on=, now=)`; `ENTRY_SIGN_IN_TEXT`, `LIVE_VIEW_LINK` |
| Page router takes the same `entry_principal` switch + server-only `clock` | `price_page_api.py` `build_price_page_router`; `main.py` passes `operational_entry_principal` |
| Entry client (dry run / save, refusal mapping, `price-entry-<32 hex>` key) | `frontend/src/sites/priceEntryClient.ts` (new) |
| Inline form, words file `PRICE_ENTRY_WORDS`, states | `frontend/src/sites/SitePriceEntry.tsx` (new) |
| Frame wiring: form via the `renderBelow` seam on `entry.keys` rows when `enabled`; `?key=` opens on arrival; re-read after save keeps the old body on screen; known_at live-view line + link without `known_at` | `frontend/src/shell/SitePricesFrame.tsx` |
| CSS (all font sizes `var(--text-*)`; one column ≤760 px) | `frontend/src/sites/sitePrices.css` (`.price-entry*`) |

Flow: closed ("Set a new price") → open (Amount + unit suffix, Currency fixed text when a series exists else
select, Basis radios, Where this price comes from, Applies from = `entry.today`) → Continue = dry run → confirm panel
with the server's one sentence (default 8) and Reason when `reason_required` (Save waits for it) → Saving… →
success note = server `summary` (it says figures read "Updating…" for a few minutes) + "← Back to where you were";
the page re-reads (row value, History "Entered by site admin"). Refusals show the server message + "Check: <fields>."
+ "Nothing was saved."; REASON_REQUIRED on save reopens Reason; 503 "Prices cannot be saved right now. Nothing was
saved."; network loss on save "We could not confirm the save. Saving again is safe." with the same key.

### Form-half deviations (Architect to confirm)

7. **`entry` carries four fields beyond `{enabled, keys}`:** `today` (Site-local date; the browser has no Site zone),
   `unit_text` (unit suffix for a key with no price yet), `currencies` (the select for a key with no series; sorted
   `ISO_4217`, default USD), `live_view` (the known_at honest-state words, server-side). All empty/None when disabled.
8. **Basis has no default selection**; an unchosen basis is refused by the server (`fields: ["basis"]`), shown as
   "Check: Basis."
9. **The "Set a new price" button sits in the row's slot** (`data-price-slot`) under the row, not in a table cell, so
   the PR-2a seam is the only change to the table.
10. **MOCK DEVIATION (D-PRICE.3):** v7.1 `price-it.html` has no form (Part B read-only; Part D "Comes with sign-in");
    the form layout follows rev 5 §5.3 inside Part B's table. Labelled in `SitePriceEntry.tsx`.

### Form-half checks (revision after the form-half commits)

- No-DB: `test_pr3_price_page_entry.py` (4, new) + `test_pr2a_price_page.py` + `test_pr3_price_entry.py`: **107 passed**.
- Postgres (`assetops_pr3_test`, PYTHONPATH incl. `gateway;field`): `test_pr3_price_entry_postgres.py` **4 passed,
  0 failed, 0 skipped** (JUnit tests=4), wall 34 s, after the merge; `test_pr2a_price_page_postgres.py` 4 passed.
- Vitest: `sitePriceEntry.test.tsx` **18 passed** (closed, entry off, known_at, open/`?key=`, currency select,
  confirm→saving→saved + re-read + body keys, reason required, 7 save refusals through the real client with their
  server words, dry-run refusal, 503, network loss + same-key retry, client lost mapping); `sitePrices.test.tsx` 14
  passed. Non-vacuity: forcing the form onto every row fails the "entry-key rows only" test (reverted).
- `tsc --noEmit` clean. `npm ci` replaced the `node_modules` junction (with the junction, jest-dom matchers did not
  register: two vitest instances).
- Layout evidence: `node tools/pr3-price-entry-evidence.mjs http://localhost:5496 8996 var/pr3-evidence` (fixture API,
  vite 5496; not the demo ports): open / confirm (Reason) / saved at 1440 and 390 px, **6/6 PASS** — form or note
  present with width > 0, inside the viewport, page scrollWidth ≤ viewport (1425/1440, 375/390). Captures in
  `var/pr3-evidence/` (untracked). At 390 the fields stack to one column; the success note sits under the updated
  row with the Back link.
- check-all (`tools\check-all.ps1 -Python <plan2 venv>`, on `bb61216fb`): **17/19 PASS** first run (estate guard 22 min).
  The 2 failures were real and fixed in `528b7c8f6`: (a) Evidence width check — the new evidence script's navigation
  and post-capture resize lacked `requireWidth` within 6 lines; added (`test_evidence_checks.mjs` 12 pass, 0 fail).
  (b) Architecture seams, SR-2 `page-range-forms.ps1`: "SitePriceEntry.tsx renders its own date range form (1 date
  inputs)". The one date is rev 5 §5.3's "Applies from" value recorded on the price, not a page range; added a
  **narrow, commented exemption for that one file** (Q3). `check-architecture.ps1` then passes (needs
  `ASSETOPS_GUARD_PYTHON`). The other 17 guards were not rerun (no file they read changed). → 19/19 after the fixes.

### Questions for the Architect (form half)

- **Q3** Confirm the SR-2 exemption for `SitePriceEntry.tsx` (an entry date, not a page date range), or name the
  input the price form should use instead (FocusPicker is range-scoped and would declare a "Day shown").
- **Q4** Confirm deviations 7-9 (extra `entry` fields, no default basis, button in the row slot).
- Not done: AR-4 rerun of the Postgres flow (AR-4 not on main yet).

## Resume points for the form half (Friday, on PR-2a) — done above except where noted

1. Rebase/merge onto PR-2a; add `entry: {"enabled", "keys"}` to the PR-2a page read (`enabled` false without the
   principal or under `known_at`) and the `set_by_label` map (`service:operator-entry` → "Entered by site admin").
2. Frontend `sitePriceEntry.test.tsx` and the form per rev 5 §5.3 UI + honest-states table; the server contract is
   this packet's route (dry run body/response, save 201/200 body, refusal `{"detail": {"code","message"[,"fields"]}}`).
3. Postgres additions (same file): productive-use INITIAL → mill value priced, `price_action` gone; stored Financials
   response not served after a save. Rerun the flow test after AR-4 merges.
4. Merge `task/PR-1-price-action` again if it moves; renumber 0060 if another branch takes it first.
5. **CSS rule (Architect rev 6, UQ-FI, main `982167625`):** any CSS the form adds uses `var(--text-*)` tokens for
   font sizes only, never a literal px font size. (The server half adds no CSS.)
6. Run Postgres files with PYTHONPATH including the worktree's `gateway;field` (else chain fixtures start a stale
   gateway). A fresh worktree has no `frontend/node_modules`; the missing-claim guards need it (a junction to the
   main checkout's `node_modules` was used here, untracked).
