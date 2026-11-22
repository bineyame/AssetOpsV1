# DDR: the deep-dive rehearsed end to end on emulated exports (implementer spec)

Status: in_review (build 2026-11-21, `packet.md`); rev 4, 2026-11-22: §5.2 step 3 gains the two cursor keys (D-DDR.16); rev 3, Architect (Claude), 2026-11-21: handshake round 2 answered (`rulings.md`, "Handshake answers (round 2)",
D-DDR.11 to D-DDR.15; D-WK.12 for the one-figure read); rev 2 answered round 1. Lane B, the deep-dive path's last unit
(`two-week-build-plan.md` §0.1 row 14; D-BW1.11). **1.5 units** (rev 2: 1.25; +0.1 codes and facts, D-DDR.11; +0.1 the
runbook order and ON1's runbook test, D-DDR.15; +0.05 the key check, R17). Day-14 order (D-WK.14): 3C2 unit 2, then
WK's world build and check, then WK, then DDR's merge and rehearsal; DDR builds beside them (D-DDR.14). Verification
review (W5) of a non-product check, discovery for the one store read it adds.
- **What it proves.** A person in the Analyst role takes Lakeside's exports, with the budget in a shape the product has
  never seen, from onboarding to the one screen with no code change, by the runbook alone; the screen meets step 5's
  gate (Lakeside October 1,443.00 against 2,295.00, −852.00; Kobo −562.00 as +38.00 and −600.00, to the cent);
  "not yet reconciled" is shown honestly first and lifted only by a matching statement; the first agreed change is an
  Action (RC9). A verifier fails if any step that leaves a record was skipped.
- **Builds on (all merged before DDR builds):** `ON1` (`onboard_operator`, the Lakeside onboarding fixture, the
  runbook), `3A3` (`tools/world_history.py exports`, `load_emulated_exports`), `3A6` (`source_profile admit`,
  admitted readers in the loader), `3A2` (intake), `3A7` (`reconcile_month`), `4b`, `5a`, `3B7a`
  (`build_structure_snapshot`), `5b`, `4d` (litre notes), `5c` (`DeepDiveRead`, `GET /api/portfolio/month`), `3C2`
  (`record_action` and `build_agreed_actions`: `specs/3C2-agreed-change-action/spec.md`, both units; unit 2 may merge
  while DDR builds, D-DDR.14).
- **Decisions:** `rulings.md` (D-DDR.1 to D-DDR.10). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/DDR-rehearsal` off `main` now (every unit above is merged but 3C2 unit 2); worktree
  `/opt/assetecon/AssetOpsV1-ddr`. Build S1 to S10, G1 to G9 and tests 3 to 8 first; write G10 and test 1's S11 and
  S12 lines to the spec, and run them once `main` holds 3C2 unit 2 (merge `main` in; `git grep -n StoreAgreedActions
  -- backend/assetops_backend/deep_dive/composition.py` shows a line). The packet goes to review only from such a base
  (D-DDR.14). DDR merges only after WK's run (WK spec §5) has passed its step 5, never between WK's steps 3 and 5.
- **Read:** `rulings.md`; `Docs/engineering/operator-deep-dive-runbook.md`; 3A6 `spec.md` §2.1, §2.4, §2.5, §2.7,
  §2.8, §4.2; 5c `spec.md` §3.5 and §4; 3B7a `spec.md` §3.1, §4.4; 3A7 `spec.md` §5.
- **Databases:** the tests use one pooled `*_test` database per run (`tools/heavy-slot.sh --db`). The rehearsal itself
  (§5) runs on `assetops_rehearsal_ddr1_test` (runbook `assetops_rehearsal_${REHEARSAL}_test`, D-DDR.12), created and
  dropped by the coordinator (runbook steps 2 and 12); no agent creates or drops a database. Never ports 5490 or 8990, the walkthrough database or Docker.
- **No product code** except `assetops_backend/rehearsal_check.py` and one read on the snapshot store (§2.3). The new
  budget layout is data only (D-DDR.2). Edited outside the backend package: the two runbook copies and
  `backend/tests/test_on1_served_tenant.py`'s runbook table (§6, D-DDR.15). No statement, no SC-1 baseline or
  allow-list edit (D-DDR.11).

## 1. The steps (the runbook's order; each a command a person runs)

| # | Step | Command (inside the runbook's `( ... )` settings block) | Leaves |
|---|---|---|---|
| S1 | Onboard Lakeside | `onboard_operator digest`, `check`, `apply` with `backend/tests/fixtures/on1/lakeside-power.onboarding.json` (runbook step 4) | tenant, Sites, people, roles, key |
| S2 | Admit the board's budget layout | `source_profile admit --tenant lakeside-power --profile backend/tests/fixtures/ddr/ddr-board-budget.profile.json --sample backend/tests/fixtures/ddr/ddr-board-budget.xlsx --expected backend/tests/fixtures/ddr/ddr-board-budget.expected.json --as wanjiru@lakeside-power.example` (its output's `admitted_by` is Wanjiru's id, used in S6) | admitted profile |
| S3 | Write the exports; put the board budget in place of the emulated one | `python tools/world_history.py exports --manifest Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml --out "$DIR" --tenant lakeside-power`; `rm "$DIR/lakeside-power.budget.csv"`; `cp backend/tests/fixtures/ddr/ddr-board-budget.xlsx "$DIR/lakeside-power.profile.ddr-board-budget.xlsx"` | files only |
| S4 | Submit and accept | `load_emulated_exports --dir "$DIR" --tenant lakeside-power --submit-as wanjiru@lakeside-power.example --accept-as joseph@lakeside-power.example` | accepted uploads, records |
| S5 | The finance lead's first figures | `reconcile_month record --tenant lakeside-power --as joseph@lakeside-power.example --period 2026-10 --currency USD --revenue 9700.00 --fuel-cost 5100.00 --source-ref "Management accounts, October 2026, draft"` | statement 1 (not matched) |
| S6 | Prepare the month | `build_structure_snapshot build --tenant lakeside-power --month 2026-10 --by person:<Wanjiru's id from S2>` | snapshot A |
| S7 | Read the screen | `GET /api/portfolio/month?month=2026-10` (browser: `/portfolio/month?month=2026-10`) | none (a read) |
| S8 | The corrected figures | as S5 with `--fuel-cost 5000.00 --source-ref "Management accounts, October 2026, final"` | statement 2 (opens) |
| S9 | Prepare the month again | as S6 | snapshot B |
| S10 | Read the screen | as S7 | none |
| S11 | Record the agreed change | `record_action --tenant lakeside-power --as amina@lakeside-power.example --title "Lower the generator stop setting at Kobo to 70% battery charge" --owner peter@lakeside-power.example --due 2026-12-15 --site KOBO-001 --factor candidate_l` | an Action |
| S12 | Read the screen; then check | as S7; then `python -m assetops_backend.rehearsal_check --tenant lakeside-power --month 2026-10` | none |

Runbook sections (§6, D-DDR.15): S1 section 4; S2 section 6; S3 and S4 section 7 (write, replace, load: three blocks);
S5 and S8 section 8; S6 and S9 section 9; S7, S10 and S12's read section 10; S11 and S12's check section 11.

## 2. The checker (`assetops_backend/rehearsal_check.py`)

### 2.1 The command

`python -m assetops_backend.rehearsal_check --tenant SLUG --month YYYY-MM [--expect PATH]`; `--expect` defaults to
`backend/tests/fixtures/ddr/lakeside-2026-10.expect.json`. `DATABASE_URL` and `ASSETOPS_PSEUDONYM_KEY_DIR` from the
environment (R17). `build_parser()` and `main(argv, *, services=None)` (tests inject; ON1's runbook test parses the
command through `build_parser`). Exit 2 before any read, the code alone on stderr: `NO_DATABASE`, `NO_KEY_DIR`,
`UNKNOWN_TENANT` (through `AccountService.tenant_by_slug`), `BAD_MONTH`, `EXPECT_UNREADABLE`. Otherwise every gate
runs in order; stdout one JSON line per gate `{"gate": "G<n>", "step": "S<n>" | null, "state": "PASS" | "FAIL",
"code", "facts"}` (PASS: `code` null, `facts` `{}`; FAIL: §2.4's code and facts); exit 0 when all pass, else 4 with
`DDR_GATE_FAILED G<n> <CODE>` on stderr for the **first** failure. No English anywhere in the module: codes and facts
only (D-DDR.11). It writes nothing, and it prints no path under the key folder and no key content (D-DS4.19).

### 2.2 The gates (each reads the records its step leaves, never the previous gate's output; D-DDR.3)

| Gate | Step | Passes when |
|---|---|---|
| G1 | S1 | the tenant exists; its Sites are exactly KISIWA-001, KOBO-001, MTO-001, each MINIGRID; held grants give exactly one OPERATOR_EXECUTIVE (amina), at least one FINANCE_AND_COMMERCIAL_LEAD (joseph) and ANALYST (wanjiru), granted by `service:onboarding`; the tenant's pseudonym key is usable through 3A2's `PseudonymKeys` port over `ASSETOPS_PSEUDONYM_KEY_DIR` (`commercial/pseudonym.py:126-138`; missing, erased or unusable is FAIL `KEY_STATE`) |
| G2 | S2 | the latest `ddr-board-budget` profile of the tenant is ADMITTED, version 1, admitted by Wanjiru, its profile and sample SHA-256 equal the fixture files' |
| G3 | S3, S4 | the tenant's accepted uploads (3A3 §2.8's held read) include readers `billing-illustrative-1`, `collections-illustrative-1`, `expenses-illustrative-1` and `profile.ddr-board-budget.v1`, and none `budget-illustrative-1`; each was submitted by Wanjiru and accepted by Joseph |
| G4 | S4 | for 2026-10, through `build_structure_read(url).read.site_inputs` and `build_target_read(url)`: the expectation file's stated revenue, fuel cost, O&M and staff per Site (Kisiwa O&M absent, cause NOT_RECEIVED), `collected` and `in_transit` per Site, `diesel_price` valued with every source `commercial:`, target contributions, and Kisiwa's `TargetCheck` compared by field name (`structure/targets/read.py:43`): `factor_id` contribution, `stated` −60.00, `computed` −65.00, `currency` USD, `agrees` False (I4) |
| G5 | S5 | the tenant's earliest organisation statement for the month has revenue 9700.00 and fuel cost 5100.00, `recorded_by_script` true, recorded by Joseph, stored result NOT_MATCHED |
| G6 | S6 | some portfolio snapshot of the month built by `person:<Wanjiru's id>` has `as_of` after G5's statement and, when a later organisation statement exists, before G7's, with `asked` the three codes |
| G7 | S8 | a later organisation statement for the month, recorded by Joseph, opens the gate (3A7 `check(...).opens`) |
| G8 | S9 | the latest portfolio snapshot was built by `person:<Wanjiru's id>`, its `as_of` is after G7's statement and after every accepted upload, and it is served current |
| G9 | — | `read, dispose = build_deep_dive_read(url)` (disposed in `finally`); `read.month(TenantRef(id, slug, name), "2026-10", names)`, the `TenantRef` and `names` through `ImportedSiteRegistry` (`sites/cutover.py`) as the route does (`deep_dive_api.py:49,58`; I3), equals the expectation file's `screen` entries on §3.4's compared keys; `state` SERVED, `fresh.current` true, `fresh.untracked_text` null (D-DDR.7) |
| G10 | S11 | `build_agreed_actions(url).service.for_tenant(tenant)[0]` is titled as S11, created by Amina, owned by Peter, due 2026-12-15, at KOBO-001 on `candidate_l`; the body's `actions.rows[0].title` is that title (D-DDR.9) |

### 2.3 The one store read (`structure_snapshot`)

`StructureSnapshotStore.portfolio_history(tenant_id, period) -> tuple[SnapshotRow, ...]`: every portfolio row of the
tenant and period, by `as_of`; in the memory store and the Postgres adapter (one `SELECT`, no lock). Nothing else in
3B7a changes; the persistence guard is unaffected (a read).

### 2.4 The failure codes (D-DDR.11; facts are identifiers, codes, figures as plain strings such as "1443.00", times as UTC ISO seconds, and JSON paths; never a screen string)

| Gate | `code` (`facts` keys) |
|---|---|
| G1 | `TENANT_SITES` (expected, found: lists of `CODE:TYPE`); `GRANTS` (role, expected, found: emails); `GRANTED_BY` (email, found); `KEY_STATE` (state: MISSING, ERASED or UNUSABLE) |
| G2 | `PROFILE_MISSING` (profile); `PROFILE_STATE` (status, version); `ADMITTER` (expected, found: person ids); `PROFILE_SHA` (file: profile or sample, expected, found) |
| G3 | `READER_MISSING` (reader); `READER_PRESENT` (reader); `SUBMITTER` (reader, expected, found); `ACCEPTER` (reader, expected, found) |
| G4 | `FIGURE` (site, factor, expected, found; found null when absent); `NOT_ABSENT` (site, factor, found); `CAUSE` (site, factor, expected, found); `PRICE_SOURCE` (site, source); `TARGET` (site, field, expected, found) |
| G5 | `STATEMENT_MISSING` (period); `STATEMENT_FIELD` (field, expected, found); `RECORDER` (expected, found); `RESULT` (expected, found) |
| G6 | `SNAPSHOT_MISSING` (period, built_by); `BEFORE_STATEMENT` (as_of, recorded_at); `AFTER_NEXT_STATEMENT` (as_of, recorded_at); `ASKED` (expected, found) |
| G7 | `STATEMENT_MISSING` (period); `RECORDER` (expected, found); `GATE_SHUT` (result) |
| G8 | `SNAPSHOT_MISSING` (period); `BUILDER` (expected, found); `BEFORE_STATEMENT` (as_of, recorded_at); `BEFORE_UPLOAD` (as_of, accepted_at); `NOT_CURRENT` (reason: the freshness code) |
| G9 | `STATE` (found); `NOT_CURRENT` (reason); `UNTRACKED`; `SCREEN` (path: the first differing JSON path among §3.4's compared keys, in key order; no values) |
| G10 | `ACTION_MISSING`; `ACTION_FIELD` (field, expected, found); `SCREEN_NOT_CONNECTED`; `SCREEN_ROW` (field) |
| any | `READ_FAILED` (store: the composition name); that gate FAILs and the later gates still run |

A gate reports its first failing condition in the table's order. Tests assert codes and facts, never prose.

## 3. Fixtures (hand-written; never produced by the code under test, W2)

### 3.1 `backend/tests/fixtures/ddr/ddr-board-budget.xlsx` (a shape never seen: D-DDR.2)

Written by `backend/tests/fixtures/ddr/make_board_budget.py`, which imports `build_workbook` from
`backend/tests/fixtures/3a6/make_budget_xlsx.py` (sheet `Board pack FY26`). Text cells `inlineStr`; no number cells.
The bytes are committed. The generator is byte-stable (R9): it writes (or rewrites `build_workbook`'s output into) a
zip whose members keep one fixed order, each `ZipInfo` with `date_time (2026, 7, 2, 0, 0, 0)`, `ZIP_DEFLATED` at level
9, `create_system 0` and no extra fields; test 7 proves it.

| r | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| 1 | Lakeside Power – Board budget FY2026 | | | | | |
| 2 | Approved 2 July 2026 | | | | | |
| 3 | Line ID | Site | Period | Budget line | Amount | Ccy |
| 4 | BB-01 | KOBO-001 | October 2026 | Revenue | 3,420.00 | USD |
| 5 | BB-02 | KOBO-001 | October 2026 | Fuel | 875.00 | USD |
| 6 | BB-03 | KOBO-001 | October 2026 | O&M | 600.00 | USD |
| 7 | BB-04 | KOBO-001 | October 2026 | Salaries | 500.00 | USD |
| 8 | BB-05 | KOBO-001 | October 2026 | Contribution | 1,445.00 | USD |
| 9 | BB-06 | KISIWA-001 | October 2026 | Revenue | 4,125.00 | USD |
| 10 | BB-07 | KISIWA-001 | October 2026 | Fuel | 2,990.00 | USD |
| 11 | BB-08 | KISIWA-001 | October 2026 | O&M | 700.00 | USD |
| 12 | BB-09 | KISIWA-001 | October 2026 | Salaries | 500.00 | USD |
| 13 | BB-10 | KISIWA-001 | October 2026 | Contribution | (60.00) | USD |
| 14 | BB-11 | MTO-001 | October 2026 | Revenue | 2,240.00 | USD |
| 15 | BB-12 | MTO-001 | October 2026 | Fuel | 375.00 | USD |
| 16 | BB-13 | MTO-001 | October 2026 | O&M | 500.00 | USD |
| 17 | BB-14 | MTO-001 | October 2026 | Salaries | 450.00 | USD |
| 18 | BB-15 | MTO-001 | October 2026 | Contribution | 915.00 | USD |
| 19 | BB-16 | (empty) | October 2026 | Salaries | 1,200.00 | USD |

(The lines are 5a's `targets_lakeside.json` steps 1 and 2, less Kobo's unused `diesel_cost`; the Kisiwa contribution
line −60.00 is the deliberate disagreement with its lines' −65.00. Do not correct it.)

### 3.2 `ddr-board-budget.profile.json` (3A6 §2.1)

`schema` `assetops.source-profile`, `schema_version` 1, `profile_id` `ddr-board-budget`, `status` ILLUSTRATIVE,
`source_type` `budget_workbook`, `source_system` `lakeside-board-pack`, `file` `{"format": "xlsx", "sheet": "Board pack
FY26", "header_row": 3}`, `values` `{"decimal_mark": ".", "thousands_mark": ",", "negative": "parentheses",
"date_format": "DD/MM/YYYY", "time_format": "HH:MM", "month_format": "Month YYYY", "timezone": "Africa/Nairobi"}`,
`version` `{"from": "constant", "value": "1"}`, columns: `Line ID` → `source_record_id` (text) · `Site` → `site_code`
(text) · `Period` → `clocks.recognition_period` (month) · `Budget line` → `body.factor_id` (text, map `{"Revenue":
"revenue", "Fuel": "fuel_cost", "O&M": "om", "Salaries": "staff", "Contribution": "contribution"}`) and
`body.line_ref` (text) · `Amount` → `body.value` (number) · `Ccy` → `body.currency` (text); `constants` `{"kind":
"BUDGET_LINE", "body.version_ref": "board-budget-fy26"}`; `personal` `[]`.

### 3.3 `ddr-board-budget.expected.json` (3A6 §4's expected-file form)

Sixteen BUDGET_LINE records in row order: `format_version` 1, `source_record_id` the Line ID, `source_version` "1",
`site_code` the Site (absent for BB-16), `clocks.recognition_period` "2026-10", `body` `{"factor_id", "line_ref" (the
native text: "Revenue", "Fuel", "O&M", "Salaries", "Contribution"), "value" (plain: "3420.00", "875.00", "600.00",
"500.00", "1445.00", "4125.00", "2990.00", "700.00", "500.00", "-60.00", "2240.00", "375.00", "500.00", "450.00",
"915.00", "1200.00"), "currency": "USD", "version_ref": "board-budget-fy26"}` (3A6 §2.4: marks removed, parentheses
negative, fraction digits kept).

### 3.4 `lakeside-2026-10.expect.json` (the checker's literals)

`sites`, `people` (G1); `profile` with the two SHA-256 of §3.1 and §3.2's files, computed by `make_board_budget.py`
and written in by hand (G2); `readers` (G3); per Site `stated` {revenue, fuel_cost, om, staff, collected, in_transit}
and `target_contribution` (G4): KISIWA-001 4070.00, 3120.00, absent, 500.00, 3800.00, 0.00, −65.00; KOBO-001 3458.00,
1475.00, 600.00, 500.00, 3180.00, 0.00, 1445.00; MTO-001 2160.00, 400.00, 500.00, 450.00, 1890.00, 150.00, 915.00 (3A3
E2 to E5); `statements` (G5, G7); `action` (G10: the title, "Amina", "Peter", "2026-12-15", "KOBO-001",
"candidate_l").

`screen` (G9; D-DDR.7). **Compared keys:** `schema`, `operator`, `month`, `month_words`, `state`, `standing`,
`headline`, `status_line` after its first sentence, `tiles`, `notices`, `bridge`, `cash`, `outcomes`, `decisions`,
`not_available`; `fresh.current` true and `fresh.text`, `fresh.untracked_text` null. **Ignored:** `as_of`,
`as_of_text`, the status line's first sentence, `nav`, `state_text`, `actions` (G10's). The values are 5c §3.5 World
B's with these differences only: names "Kisiwa mini-grid", "Kobo mini-grid", "Mto mini-grid"; `asked` order
KISIWA-001, KOBO-001, MTO-001 (3B7a builds over `tenant_sites`, by code), so every Site list and the by-Site rows
follow it; the notice "Kisiwa mini-grid's budget states a contribution of −$60.00; its budget lines add to −$65.00.
The target used is −$65.00."; the status line after its first sentence "Reconciled with the management accounts.
Kisiwa mini-grid's budget disagrees with its own lines."; each Site's fuel cost text "Not split further until the EMS
interval export (generator running and output, solar available power, battery charge), the generator's fuel curve
(litres per kWh; litres per hour idle), tank dips at the start and end of the month, fuel delivery notes and a
generator and a fuel tank declared in the Site's setup (litres are worked out for each)." (4d: no Site declares a fuel
tank, `GENERATOR_OR_TANK_NOT_DECLARED`; the wording `main` renders, `i18n/statements/en/vocabulary.py:85`, R14); and
the not-available row "a generator and a fuel tank declared in the Site's setup (litres are worked out for each) · Diesel not shown to be avoidable, Diesel run
while solar and battery could carry the load and Unexplained fuel · Kisiwa mini-grid, Kobo mini-grid and Mto
mini-grid" after the service contractor's invoices row. The test's own read after S7 compares 5c World A's figures,
its standing text and its status line after the first sentence ("Not yet reconciled with the management accounts.
Kisiwa mini-grid's budget disagrees with its own lines.").

**Where the literals come from (R14, W2).** The `screen` literals are transcribed by hand from 5c's merged World B test
literals (`backend/tests/test_5c_deep_dive_view.py`, World B, and the setup and fuel texts it asserts) plus the
differences above, never from a run. Any other wording that differs between this section and `main` is a mid-build
question (it stops only that literal), never a silent edit. **One figure (D-WK.12):** the reviewer reads the file's
`screen` for any quantity shown twice; the allowed pairs are Kisiwa's budget notice (stated against its lines) and plan
against actual, and the statement against the records only while they do not match (S7). Kobo's stop-70 litres and
value read "Not available yet". A breach is a product finding for the Architect, not fixed in DDR.

## 4. Tests (`backend/tests/test_ddr_rehearsal_postgres.py`, pooled `--db`; one pooled database per run)

Each case starts from empty tables (`pg_harness.empty_tables`) with fresh temporary folders for `$DIR` and the key
(D-DDR.10). Each step runs in-process through its command's `main(argv)` (S3 through `subprocess` for the tool), with
the settings the runbook sets (`DATABASE_URL`, `ASSETOPS_TENANT_SLUG=lakeside-power`, `ASSETOPS_PSEUDONYM_KEY_DIR`),
`record_action` with its clock injected at the test's real now, and the screen through `TestClient(create_app())`.
Every checker run prints ten lines (R7); every FAIL is asserted by its §2.4 code (and the facts named in the test).
1. **The rehearsal, with progress.** S1 to S12 in order: every command exits 0; after each step the checker's first
   failing gate is: S1 → G2; S2 → G3; S3 → G3; S4 → G5; S5 → G6; S6, S7 → G7; S8 → G8; S9, S10 → G10 (this is also
   "no S11 → G10"); S11, S12 → none (exit 0, ten PASS lines). S7's body has World A's figures, standing text and
   status line (after its first sentence), every money word suffixed ", not yet reconciled"; S10's is reconciled;
   S12's shows the Action first.
2. *(folded into test 1, D-DDR.10)*
3. **Skips** (each a fresh case running every step but the one named): no S5 → G5 fails; no S6 → G6 fails; no S8 →
   G7 fails; no S9 → G8 fails; S3 without the replacement (the emulated budget loaded) → G3 fails; no S2 → S4 exits 2
   `PROFILE_NOT_ADMITTED` and G2 fails.
4. **Shortcuts.** (a) S4 replaced by writing the same records through 3A1's service directly (no upload): G3 fails.
   (b) S6 run with `--by service:shortcut` (S7 to S12 as written): G6 fails.
5. **No code for the new layout.** `git diff main...HEAD --stat` lists no file under `backend/assetops_backend/` or
   `contracts/` but `rehearsal_check.py` and §2.3's read; the profile lives under `backend/tests/fixtures/ddr/`.
6. `portfolio_history`: two builds give two rows by `as_of` (memory and Postgres).
7. *(no database; `backend/tests/test_ddr_rehearsal_check.py`)* `make_board_budget.py` run into a temporary folder writes bytes equal to the committed XLSX, and
   their SHA-256 equals the expectation file's literal.
8. *(no database; the same file; `main(argv, services=…)` with injected reads)* (a) G2 FAIL when the profile's admitter is Joseph;
   (b) G6 and G8 FAIL when the snapshots were built by `service:x`; (c) G9 PASS when only `as_of`, `as_of_text`, the
   status line's first sentence and `nav` differ from the file, FAIL when one figure differs; (d) G4 FAIL with Kobo's
   `collected` 3000.00; (e) G10 FAIL when the store's newest Action is owned by Halima; (f) with no
   `ASSETOPS_PSEUDONYM_KEY_DIR`, exit 2 `NO_KEY_DIR` and no gate line; with an erased key, G1 `KEY_STATE` ERASED;
   (g) the source of `rehearsal_check.py` passes `tools/checks/statement_catalogue.py` with no new finding (no
   `HAND_BUILT_NEW`), and every stdout and stderr line of tests 1 and 8 parses as §2.1's JSON or `DDR_GATE_FAILED G<n>
   <CODE>` (D-DDR.11).
9. *(no database)* ON1's runbook tests pass on the edited runbook (`backend/tests/test_on1_served_tenant.py -k
   runbook`): the command list is D-DDR.15's, both copies are identical, and every line naming a rehearsal database
   reads `assetops_rehearsal_${REHEARSAL}_test`.

**Runtime.** While building, run test 1 alone (`-k rehearsal`) and tests 5 to 8; tests 3 and 4 once before review.
The packet records the module's wall time; the cap for a run is twice it.

## 5. The rehearsal itself (the coordinator, after merge)

### 5.1 The run

After WK's run has passed its step 5 and DDR has merged (D-WK.14), with no other heavy database job running, the
coordinator creates `assetops_rehearsal_ddr1_test` (runbook step 2, `REHEARSAL=ddr1`) and the key folder (step 3,
`/opt/assetecon/keys/assetops_rehearsal_ddr1_test`); the analyst role (an agent following the runbook only, no other
instructions) runs S1 to S12 on it; the coordinator records each step's wall time and every place the runbook was
unclear in `specs/DDR-rehearsal/packet.md`. The served tenant on that database is what the owner walks for 5c
(5c spec §9; D-WK.9). Erase (runbook step 12) after the owner's walkthrough, after §5.2's stop.

### 5.2 Serving it for the owner's walk (D-DDR.13; owner-level, owner-away row 65)

The coordinator only, in the 13 Nov shape and with WK §3.5's environment list, on **8992 (API) and 5492 (web)**. Never
8990/5490 (the 13 Nov serve), never 8991/5491 (WK), never `assetops_polish_walk*_test`, `/opt/assetecon/AssetOpsV1-walk`
or any `/opt/assetecon/AssetOpsV1-wk*` worktree.
1. **Tree.** `S` is the commit to serve: the 5c unit 3 branch's reviewed head when its review has passed (the owner
   walks 5c's screen before its merge), else `main`. It must contain 3C2 unit 2's merge (`git merge-base
   --is-ancestor <that merge> S`), and `git diff --quiet R S -- backend/migrations` must hold, `R` being the `main`
   commit the rehearsal database was migrated at (runbook step 2). Then `git -C /opt/assetecon/AssetOpsV1 worktree add
   --detach /opt/assetecon/AssetOpsV1-ddrserve S` and `ln -s /opt/assetecon/AssetOpsV1/frontend/node_modules
   /opt/assetecon/AssetOpsV1-ddrserve/frontend/node_modules`.
2. **Ports free.** `ss -ltn` shows nothing listening on 8992 or 5492; otherwise stop and report (never kill an unknown
   listener).
3. **API**, from `/opt/assetecon/AssetOpsV1-ddrserve/host`, the environment built with `env -i`, never inherited:
   `PATH`, `HOME`, `LANG`; `PYTHONPATH` the tree's `backend`, `contracts`, `gateway`, `simulator`, `host` joined by
   `:`; `DATABASE_URL` the rehearsal URL (runbook step 2's form); `ASSETOPS_TENANT_SLUG=lakeside-power`;
   `ASSETOPS_PG_PORT`, `ASSETOPS_PG_PASSWORD` when the coordinator's shell holds them; `PYTHONUNBUFFERED=1`;
   `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` and `ASSETOPS_WORK_CURSOR_KEY_HEX`, each a fresh
   `python -c 'import secrets; print(secrets.token_hex(32))'` per serve, never written to a file or log (D-DDR.16). Never
   `ASSETOPS_PSEUDONYM_KEY_DIR` (commercial uploads stay off), `ASSETOPS_REAL_OPERATOR_DATA`,
   `ASSETOPS_OPERATIONAL_ENTRY`, any `ASSETOPS_READING_UPLOAD_*` or `ASSETOPS_GATEWAY_*` name,
   `ASSETOPS_PERIOD_READ_KINDS`, or a `PG*` name. Command: `setsid /opt/assetecon/AssetOpsV1/.venv/bin/python -m uvicorn
   lab_app:app --host 127.0.0.1 --port 8992`, stdout and stderr to
   `/opt/assetecon/AssetOpsV1-ddrserve/var/rehearsal_ddr1/logs/api.log`.
4. **Web**, from `/opt/assetecon/AssetOpsV1-ddrserve/frontend`, `env -i PATH HOME LANG ASSETOPS_API_PORT=8992`:
   `setsid npm run dev -- --port 5492 --strictPort --host 127.0.0.1`, logs beside the API's.
5. **Up.** Within 120 s `curl -fsS http://127.0.0.1:8992/api/health` answers 200 and 5492 accepts a connection, else
   stop both (step 7) and report the log paths. Record both PIDs and their `/proc/<pid>/cmdline` in the packet.
6. **Owner access** as on 13 Nov: `ssh -L 5492:127.0.0.1:5492 <server>`, then
   `http://127.0.0.1:5492/portfolio/month?month=2026-10`.
7. **Stop**, before the erase: for each recorded PID whose `/proc/<pid>/cmdline` still equals the recorded one, SIGTERM
   to its process group, 10 s, then SIGKILL; a PID that no longer matches is left and reported. Then `git -C
   /opt/assetecon/AssetOpsV1 worktree remove /opt/assetecon/AssetOpsV1-ddrserve`.

## 6. The runbook (`Docs/engineering/operator-deep-dive-runbook.md` and its verbatim source `specs/ON1-operator-tenant/runbook.md`)

Both copies get the same edit (D-ON1.19: ON1's test 3 requires them identical below the source's header). The order
is D-DDR.15's: the layout is admitted **before** the exports are written and loaded.

- **Sections.** 1 to 5 unchanged in meaning. New **6 "Admit an export layout the product has not seen"** (S2; the
  profile, its sample and the expected records; "an admitted layout is data, not code"; copy `admitted_by` from its
  output line into `ADMITTED_BY` for section 9). One paragraph: "If an export has several sheets or merged headers, no
  profile can read it: reshape it into the template by hand (a workaround) and note the minutes it took." Old 6
  becomes **7 "Receive the exports"**, three blocks: write (`world_history.py exports`), replace (plain `rm` and `cp`
  lines, S3: the sentence "When a layout admitted in section 6 replaces an emulated file, put it in place now"), load
  (`load_emulated_exports`). **8 "Record the management-accounts figures"** (S5 and S8; one block with `PERIOD`,
  `REVENUE`, `FUEL_COST`, `SOURCE_REF`; the text gives the rehearsal's draft values and then its final values; the
  finance lead reads the figures, the command records them in their name). **9 "Prepare the month"** (S6, S9; `--by
  "person:$ADMITTED_BY"`; "after every accepted import, every statement and every deploy": a deploy can change how
  figures are worked out). **10 "Show the month"** (S7, S10: the URL, what each section answers, and that "not yet
  reconciled" is expected until the figures match). **11 "Record the agreed change"** (S11's `record_action` block,
  then S12's `rehearsal_check` block: "every line PASS means every step left its record"). Old 7 becomes **12
  "Erase"**.
- **Intro.** The coordinator's steps "2, 3 and 12"; the analyst's "1, 4, 6, 7 (write and submit), 9 and 11"; the
  finance lead's "7 (accept) and 8"; "No agent runs steps 2, 3 or 12". Section 4's "`TENANT_ID` in step 7" becomes
  "in step 12".
- **Names (D-DDR.12).** Every line naming the rehearsal database or its key folder reads
  `assetops_rehearsal_${REHEARSAL}_test` (sections 2, 3, 4, 7 to 11 and 12; the braces are needed). The
  "Shell variables" line adds `ADMITTED_BY`, `PERIOD`, `REVENUE`, `FUEL_COST`, `SOURCE_REF`.
- **ON1's runbook test** (`backend/tests/test_on1_served_tenant.py`, its section 3 table only): `EXPECTED` becomes
  `["onboard_operator digest", "onboard_operator check", "onboard_operator apply", "accounts.onboard set-password",
  "source_profile admit", "world_history exports", "load_emulated_exports", "reconcile_month record",
  "build_structure_snapshot build", "record_action", "rehearsal_check", "commercial.pseudonym_key erase"]`; `_parsers`
  gains `source_profile`, `reconcile_month`, `build_structure_snapshot`, `record_action` and `rehearsal_check` (each
  module's `build_parser`); `VALUES` gains `"ADMITTED_BY": "00000000-0000-0000-0000-000000000002"`, `"PERIOD":
  "2026-10"`, `"REVENUE": "9700.00"`, `"FUEL_COST": "5100.00"`, `"SOURCE_REF": "Management accounts, October 2026,
  draft"`, and `KEY_DIR` becomes `/opt/assetecon/keys/assetops_rehearsal_ddr1_test`. No other line of that file
  changes.

## 7. Done (questions; each can fail)

1. Does the whole path run from the runbook alone, with the board's budget read by a new profile and no code change?
2. Does the screen meet step 5's gate to the cent, with Kisiwa's disagreement shown, and read "not yet reconciled"
   until the corrected statement?
3. Does the checker fail, naming the step, when any step that leaves a record is skipped or bypassed?
4. Is the agreed change an Action with its owner and due date, shown on the screen?
5. Does each gate check the person who did its step, and pass on a real clock?
6. Does each planted violation in the reviewer guide fail its named test, and is the mid-build count 0?

Packet: `specs/DDR-rehearsal/packet.md` (the test runs; after §5, the rehearsal's times and runbook notes).

## 8. Out of scope

A real operator's data (RC4; ON1b); litres (no Lakeside Site declares a tank or sends an EMS export: the screen names
them as missing); valuing the change (RC9); the sign-in page (RC7).

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | DDR waits for 3C2 | Answered (D-DDR.14, amends D-DDR.5): 3C2 unit 1 merged; unit 2 (0.25 unit, specified in 3C2 §3) is pulled first on day 14; DDR builds beside it and is reviewed only on a base holding it. G10 is not left open |
| Q4 (owner) | Who serves the rehearsed tenant, and where | The coordinator, 13 Nov shape, ports 8992 and 5492, no key folder (D-DDR.13; owner-away row 65) |
| Q5 (owner) | Two figures for one quantity on the rehearsed screen | Only Kisiwa's budget notice, plan against actual, and statement against records while unmatched (D-WK.12; owner-away row 66) |
| Q2 (owner) | Rehearse the honest mismatch first | Yes (D-DDR.4): statement 1 differs by 105.00 of fuel; the screen says so before statement 2 |
| Q3 | Who runs the rehearsal | An agent in the Analyst role with only the runbook; the coordinator times it |
