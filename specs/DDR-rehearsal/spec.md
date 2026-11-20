# DDR: the deep-dive rehearsed end to end on emulated exports (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-20. Handshake not started (`handshake.md`). Lane B, the deep-dive path's
last unit (`two-week-build-plan.md` §0.1 row 14; D-BW1.11). **1 unit.** Verification review (W5) of a
non-product check, discovery for the one store read it adds.
- **What it proves.** A person in the Analyst role takes Lakeside's exports, with the budget in a shape the product has
  never seen, from onboarding to the one screen with no code change, by the runbook alone; the screen meets step 5's
  gate (Lakeside October 1,443.00 against 2,295.00, −852.00; Kobo −562.00 as +38.00 and −600.00, to the cent);
  "not yet reconciled" is shown honestly first and lifted only by a matching statement; the first agreed change is an
  Action (RC9). A verifier fails if any step that leaves a record was skipped.
- **Builds on (all merged before DDR builds):** `ON1` (`onboard_operator`, the Lakeside onboarding fixture, the
  runbook), `3A3` (`tools/world_history.py exports`, `load_emulated_exports`), `3A6` (`source_profile admit`,
  admitted readers in the loader), `3A2` (intake), `3A7` (`reconcile_month`), `4b`, `5a`, `3B7a`
  (`build_structure_snapshot`), `5b`, `4d` (litre notes), `5c` (`DeepDiveRead`, `GET /api/portfolio/month`), `3C2`
  (`record_action` and `build_agreed_actions`, the contract in 5c spec §4.3).
- **Decisions:** `rulings.md` (D-DDR.1 to D-DDR.6). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/DDR-rehearsal` off `main` once every unit above is merged; worktree `/opt/assetecon/AssetOpsV1-ddr`.
- **Read:** `rulings.md`; `Docs/engineering/operator-deep-dive-runbook.md`; 3A6 `spec.md` §2.1, §2.4, §2.5, §2.7,
  §2.8, §4.2; 5c `spec.md` §3.5 and §4; 3B7a `spec.md` §3.1, §4.4; 3A7 `spec.md` §5.
- **Databases:** the tests use one pooled `*_test` database per run (`tools/heavy-slot.sh --db`). The rehearsal itself
  (§5) runs on `assetops_rehearsal_ddr1`, created and dropped by the coordinator (runbook steps 2 and 12); no agent
  creates or drops a database. Never ports 5490 or 8990, the walkthrough database or Docker.
- **No product code** except `assetops_backend/rehearsal_check.py` and one read on the snapshot store (§2.3). The new
  budget layout is data only (D-DDR.2).

## 1. The steps (the runbook's order; each a command a person runs)

| # | Step | Command (inside the runbook's `( ... )` settings block) | Leaves |
|---|---|---|---|
| S1 | Onboard Lakeside | `onboard_operator digest`, `check`, `apply` with `backend/tests/fixtures/on1/lakeside-power.onboarding.json` (runbook step 4) | tenant, Sites, people, roles, key |
| S2 | Admit the board's budget layout | `source_profile admit --tenant lakeside-power --profile backend/tests/fixtures/ddr/ddr-board-budget.profile.json --sample backend/tests/fixtures/ddr/ddr-board-budget.xlsx --expected backend/tests/fixtures/ddr/ddr-board-budget.expected.json --as wanjiru@lakeside-power.example` | admitted profile |
| S3 | Write the exports; put the board budget in place of the emulated one | `python tools/world_history.py exports --manifest Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml --out "$DIR"`; `rm "$DIR/lakeside-power.budget.csv"`; `cp backend/tests/fixtures/ddr/ddr-board-budget.xlsx "$DIR/lakeside-power.profile.ddr-board-budget.xlsx"` | files only |
| S4 | Submit and accept | `load_emulated_exports --dir "$DIR" --tenant lakeside-power --submit-as wanjiru@lakeside-power.example --accept-as joseph@lakeside-power.example` | accepted uploads, records |
| S5 | The finance lead's first figures | `reconcile_month record --tenant lakeside-power --as joseph@lakeside-power.example --period 2026-10 --currency USD --revenue 9700.00 --fuel-cost 5100.00 --source-ref "Management accounts, October 2026, draft"` | statement 1 (not matched) |
| S6 | Prepare the month | `build_structure_snapshot build --tenant lakeside-power --month 2026-10 --by person:<Wanjiru's id>` | snapshot A |
| S7 | Read the screen | `GET /api/portfolio/month?month=2026-10` (browser: `/portfolio/month?month=2026-10`) | none (a read) |
| S8 | The corrected figures | as S5 with `--fuel-cost 5000.00 --source-ref "Management accounts, October 2026, final"` | statement 2 (opens) |
| S9 | Prepare the month again | as S6 | snapshot B |
| S10 | Read the screen | as S7 | none |
| S11 | Record the agreed change | `record_action --tenant lakeside-power --as amina@lakeside-power.example --title "Lower the generator stop setting at Kobo to 70% battery charge" --owner peter@lakeside-power.example --due 2026-12-15 --site KOBO-001 --factor candidate_l` | an Action |
| S12 | Read the screen; then check | as S7; then `python -m assetops_backend.rehearsal_check --tenant lakeside-power --month 2026-10` | none |

## 2. The checker (`assetops_backend/rehearsal_check.py`)

### 2.1 The command

`python -m assetops_backend.rehearsal_check --tenant SLUG --month YYYY-MM [--expect PATH]`; `--expect` defaults to
`backend/tests/fixtures/ddr/lakeside-2026-10.expect.json`. `DATABASE_URL` from the environment. `main(argv, *,
services=None)` (tests inject). Exit 2 before any read: `NO_DATABASE`, `UNKNOWN_TENANT` (through
`AccountService.tenant_by_slug`), `BAD_MONTH`, `EXPECT_UNREADABLE`. Otherwise every gate runs in order; stdout one JSON
line per gate `{"gate": "G<n>", "step": "S<n>", "state": "PASS" | "FAIL", "text"}`; exit 0 when all pass, else 4 with
`DDR_GATE_FAILED G<n> <text>` on stderr for the **first** failure. It writes nothing.

### 2.2 The gates (each reads the records its step leaves, never the previous gate's output; D-DDR.3)

| Gate | Step | Passes when |
|---|---|---|
| G1 | S1 | the tenant exists; its Sites are exactly KISIWA-001, KOBO-001, MTO-001, each MINIGRID; held grants give exactly one OPERATOR_EXECUTIVE (amina), at least one FINANCE_AND_COMMERCIAL_LEAD (joseph) and ANALYST (wanjiru), granted by `service:onboarding`; the tenant's pseudonym key is readable (3A2's key store) |
| G2 | S2 | the latest `ddr-board-budget` profile of the tenant is ADMITTED, version 1, its profile and sample SHA-256 equal the fixture files' |
| G3 | S3, S4 | the tenant's accepted uploads (3A3 §2.8's held read) include readers `billing-illustrative-1`, `collections-illustrative-1`, `expenses-illustrative-1` and `profile.ddr-board-budget.v1`, and none `budget-illustrative-1`; each was submitted by Wanjiru and accepted by Joseph |
| G4 | S4 | for 2026-10, through `build_structure_read(url).read.site_inputs` and `build_target_read(url)`: the expectation file's stated revenue, fuel cost, O&M and staff per Site (Kisiwa O&M absent, cause NOT_RECEIVED) and target contributions, and Kisiwa's check `(-60.00, -65.00, False)` |
| G5 | S5 | the tenant's earliest organisation statement for the month has revenue 9700.00 and fuel cost 5100.00, `recorded_by_script` true, recorded by Joseph, stored result NOT_MATCHED |
| G6 | S6 | some portfolio snapshot of the month has `as_of` after G5's statement and before G7's, with `asked` the three codes |
| G7 | S8 | a later organisation statement for the month, recorded by Joseph, opens the gate (3A7 `check(...).opens`) |
| G8 | S9 | the latest portfolio snapshot's `as_of` is after G7's statement and after every accepted upload; it is served current |
| G9 | — | `DeepDiveRead.month(tenant, "2026-10", names)` equals the expectation file's `screen` entries (§3.2) |
| G10 | S11 | an agreed Action of the tenant with the expected title, owner Peter and due 2026-12-15 exists and is the first of the body's `actions.rows` |

### 2.3 The one store read (`structure_snapshot`)

`StructureSnapshotStore.portfolio_history(tenant_id, period) -> tuple[SnapshotRow, ...]`: every portfolio row of the
tenant and period, by `as_of`; in the memory store and the Postgres adapter (one `SELECT`, no lock). Nothing else in
3B7a changes; the persistence guard is unaffected (a read).

## 3. Fixtures (hand-written; never produced by the code under test, W2)

### 3.1 `backend/tests/fixtures/ddr/ddr-board-budget.xlsx` (a shape never seen: D-DDR.2)

Written by `backend/tests/fixtures/ddr/make_board_budget.py`, which imports `build_workbook` from
`backend/tests/fixtures/3a6/make_budget_xlsx.py` (sheet `Board pack FY26`). Text cells `inlineStr`; no number cells.

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
and written in by hand (G2); `readers` (G3); per Site `stated` {revenue, fuel_cost, om, staff} and
`target_contribution` (G4): KISIWA-001 4070.00, 3120.00, absent, 500.00, −65.00; KOBO-001 3458.00, 1475.00, 600.00,
500.00, 1445.00; MTO-001 2160.00, 400.00, 500.00, 450.00, 915.00 (3A3 E2 to E5); `statements` (G5, G7); `screen`
(G9), as 5c §3.5 World B with these differences only: names "Kisiwa mini-grid", "Kobo mini-grid", "Mto mini-grid";
`asked` order KISIWA-001, KOBO-001, MTO-001 (3B7a builds over `tenant_sites`, by code), so every Site list and the
by-Site rows follow it; the notice "Kisiwa mini-grid's budget states a contribution of −$60.00; its budget lines add
to −$65.00. The target used is −$65.00."; each Site's fuel cost text "Not split further until the EMS interval export
(generator running and output, solar available power, battery charge), the generator's fuel curve (litres per kWh;
litres per hour idle), tank dips at the start and end of the month, fuel delivery notes and the Site's generator and
fuel tank, declared in its setup." (4d: no Site declares a fuel tank, `GENERATOR_OR_TANK_NOT_DECLARED`), and the
not-available row for that record "the Site's generator and fuel tank, declared in its setup · Diesel needed to serve
the load, Diesel run while solar and battery could carry the load and Unexplained fuel · Kisiwa mini-grid, Kobo
mini-grid and Mto mini-grid"; `actions.rows[0]` as 5c World C with owner "Owner Peter · due 15 December 2026" and
"Agreed by Amina on <the day S11 ran>" (the checker compares the title, owner and due words only).
The test's own read after S7 compares 5c World A's figures and its standing text (statement 1 is the same figures as
World A's literal standing).

## 4. Tests (`backend/tests/test_ddr_rehearsal_postgres.py`, pooled `--db`; one fresh database per run)

Each step is run in-process through its command's `main(argv)` (S3 through `subprocess` for the tool), with the
settings the runbook sets (`DATABASE_URL`, `ASSETOPS_TENANT_SLUG=lakeside-power`, `ASSETOPS_PSEUDONYM_KEY_DIR` a
temporary folder), and the screen through `TestClient(create_app())`.
1. **The rehearsal.** S1 to S12 in order: every command exits 0; S7's body has World A's figures and statement 1's
   standing text with every money word suffixed ", not yet reconciled"; S10's is reconciled; S12's shows the Action;
   the checker exits 0 with ten PASS lines.
2. **Progress.** After each step the checker's first failing gate is: S1 → G2; S2 → G3; S3 → G3; S4 → G5; S5 → G6;
   S6, S7 → G7; S8 → G8; S9, S10 → G10; S11 → none.
3. **Skips** (each a fresh run of every step but the one named): no S5 → G5 fails; no S6 → G6 fails; no S9 → G8
   fails; S3 without the replacement (the emulated budget loaded) → G3 fails; no S2 → S4 exits 2
   `PROFILE_NOT_ADMITTED` and G2 fails.
4. **A shortcut.** S4 replaced by writing the same records through 3A1's service directly (no upload): G3 fails.
5. **No code for the new layout.** `git diff main...HEAD --stat` lists no file under `backend/assetops_backend/` or
   `contracts/` but `rehearsal_check.py` and §2.3's read; the profile lives under `backend/tests/fixtures/ddr/`.
6. `portfolio_history`: two builds give two rows by `as_of` (memory and Postgres).

## 5. The rehearsal itself (the coordinator, after merge)

The coordinator creates `assetops_rehearsal_ddr1` (runbook step 2) and the key folder (step 3); the analyst role
(an agent following the runbook only, no other instructions) runs S1 to S12 on it; the coordinator records each step's
wall time and every place the runbook was unclear in `specs/DDR-rehearsal/packet.md`. The served tenant on that
database is what the owner walks on day 11 (5c). Erase (runbook step 12) after the owner's walkthrough.

## 6. The runbook (`Docs/engineering/operator-deep-dive-runbook.md`)

New sections after "6. Receive the emulated exports", numbered 7 to 11, each one block as §1's commands with one
sentence of purpose: 7 "Admit an export layout the product has not seen" (S2; the profile, its sample and the
expected records; "an admitted layout is data, not code"); 8 "Record the management-accounts figures" (S5 and S8;
the finance lead reads the figures, the command records them in their name); 9 "Prepare the month" (S6, S9; after
every accepted import and every statement); 10 "Show the month" (S7: the URL, what each section answers, and that
"not yet reconciled" is expected until the figures match); 11 "Record the agreed change" (S11). "7. Erase" becomes
"12. Erase" and the intro's "steps 2, 3 and 7" becomes "steps 2, 3 and 12". Add one paragraph under 7: "If an export
has several sheets or merged headers, no profile can read it: reshape it into the template by hand (a workaround)
and note the minutes it took."

## 7. Done (questions; each can fail)

1. Does the whole path run from the runbook alone, with the board's budget read by a new profile and no code change?
2. Does the screen meet step 5's gate to the cent, with Kisiwa's disagreement shown, and read "not yet reconciled"
   until the corrected statement?
3. Does the checker fail, naming the step, when any step that leaves a record is skipped or bypassed?
4. Is the agreed change an Action with its owner and due date, shown on the screen?
5. Does each planted violation in the reviewer guide fail its named test?

Packet: `specs/DDR-rehearsal/packet.md` (the test runs; after §5, the rehearsal's times and runbook notes).

## 8. Out of scope

A real operator's data (RC4; ON1b); litres (no Lakeside Site declares a tank or sends an EMS export: the screen names
them as missing); valuing the change (RC9); the sign-in page (RC7).

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | DDR waits for 3C2 | Yes (D-DDR.5): without it S11 and G10 cannot run; if 3C2 slips past day 9, the coordinator runs S1 to S10 and DDR stays open |
| Q2 (owner) | Rehearse the honest mismatch first | Yes (D-DDR.4): statement 1 differs by 105.00 of fuel; the screen says so before statement 2 |
| Q3 | Who runs the rehearsal | An agent in the Analyst role with only the runbook; the coordinator times it |
