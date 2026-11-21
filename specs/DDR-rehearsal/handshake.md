# DDR handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4). Round 1 below; answered in
`rulings.md`, "Handshake answers (round 1)", and folded into spec rev 2.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` 93b9e23e1 (spec rev 1, `rulings.md`, `reviewer-guide.md`; owner RC1-RC9).
Severity: **High** blocks coding; Medium needs a ruling; Low is the Architect's call. **(done)** = the answer changes
what counts as done.

### High

- **R1 (done) D-DDR.5, §1 S11, §2.2 G10: 3C2 has no spec, so S11 and G10 cannot be specified or pre-flighted.** The only
  definition is 5c §4.3's contract (a command line and a port). Open: which store G10 reads (D-DDR.3 says each gate
  reads its own step's records, but G10 as written also reads "the first of the body's `actions.rows`", i.e. the
  screen); whether Amina (OPERATOR_EXECUTIVE) may create and Peter (SITE_MANAGER of KOBO-001 only, ON1 fixture) may own
  a portfolio Action; what `state_words` reads; whether the product's existing Actions (`actions/`, verification plans)
  are "Actions of the tenant". Expected: 3C2's spec (or a 3C2 section here) before this handshake closes, naming the
  store read G10 uses and the role rules; test 3 gains "no S11 → G10 fails".
- **R2 (done) §3.4 `screen`, G9: the comparison set cannot pass on a real clock.** World B's literals include
  `as_of_text` "Figures as of 20 November 2026, 08:00 UTC", `nav.next` (null only while `now` is in November), and
  `fresh`/`untracked_text`; the rehearsal builds at its own instant, and §3.4's "differences only" list omits them. G9
  also must leave `actions` to G10 (progress test 2 expects S9 and S10 to stop at G10, so G9 must pass with no Action).
  Expected: §3.4 names exactly which keys G9 compares (figures, words, notices, stop texts, not-available rows,
  outcomes, standing) and which it ignores (`as_of`, `as_of_text`, `nav`, `actions`), with `fresh.current` true and
  `untracked_text` null asserted.

### Medium

- **R3 (done) §2.2, §4 tests 3 and 4: bypasses the checker cannot see.** G2 does not check who admitted the profile
  (`--as` Wanjiru), so a profile written straight to the store passes; G6 and G8 do not check `built_by`
  (`person:<Wanjiru>`), so a snapshot built through the service passes; test 3 has no "no S8" or "no S11" case (only
  the progress test, which stops rather than skips). Expected: G2 checks the admitter, G6/G8 the builder, and test 3
  gains no S8 (G7) and no S11 (G10).
- **R4 §4 tests 1 to 4: one pooled database, a fixed slug, about eight full rehearsals.** `lakeside-power` cannot be
  onboarded twice in one database, and the pool gives one database per run. Expected: how each "fresh run" resets
  (truncate between cases, a slug per case, or one pooled database per case), and the expected runtime against the
  owner's test-suite policy (isolated runs while building).
- **R5 (done) §3.4: the screen's cash and price figures are not cross-checked by G4.** G4 compares revenue, fuel cost,
  O&M, staff and target contributions with 3A3 E2 to E5; the screen also needs collected, in transit and outstanding
  per Site (3,180.00, 0, 278.00; 3,800.00, 0, 270.00; 1,890.00, 150.00, 120.00) and a `diesel_price` from fuel invoices
  for every Site (if Mto's export lacks litres the price falls back to the declared assumption, `untracked_text` is
  not null and G9 differs). Expected: G4 also checks the cash leaves and each Site's `diesel_price` evidence, or §3.4
  says where these literals come from.
- **R6 §2.2 G6 "before G7's" when G7's statement does not exist yet.** After S6 and S7 the progress test expects G6 to
  pass and G7 to fail; say that an absent later statement leaves G6's upper bound open.

### Low

- **R7 Reviewer guide P5 (the checker stops printing after the first failure):** test 2 as written checks only the
  first failing gate; it must also assert ten lines on every run.
- **R8 G9's `names`:** the checker runs outside the app; say whether names come from the Foundation registry (as the
  route) or the tenant's Site rows.
- **R9 §3.1 the XLSX and its SHA-256:** the SHA in the expectation file is pasted from `make_board_budget.py`'s output;
  commit the XLSX bytes and keep the generator deterministic (fixed zip timestamps), or the literal drifts.
- **R10 S6 `--by person:<Wanjiru's id>`:** the runbook must show how the analyst finds that id (an `onboard_operator`
  output line or a command).
- **R11 RULES freshness:** adding `portfolio_history` changes `structure_snapshot/`, so every snapshot built before DDR
  merges reads "out of date: the way they are worked out has changed"; and any deploy between S9 and the owner's
  walkthrough makes G8 ("served current") fail. Worth one runbook line: rebuild after a deploy.

## Implementer pre-flight

Pre-flight of spec §0 to §6 against `main` 93b9e23e1 (read-only); 3A6, 3A7, 3B7a, 4d and 5c by their specs (3B7a also
on `task/3B7a-snapshot`). Verified: ON1's `lakeside-power.onboarding.json` has amina, joseph, wanjiru and peter
(SITE_MANAGER, KOBO-001), names "Amina", "Peter", Sites "Kisiwa mini-grid", "Kobo mini-grid", "Mto mini-grid"; no Site
declares a FUEL_TANK and Kisiwa declares two generators, so 4d gives `GENERATOR_OR_TANK_NOT_DECLARED` for all three
(the §3.4 fuel text and SITE_SETUP row follow, RECORDS order correct); `load_emulated_exports` reads
`<slug>.budget.csv` (`KEYS`, `load_emulated_exports.py:41,83`) and refuses `EXPORT_PATHS_MIXED`; `world_history.py
exports` exists; 3A6 admits the board profile as written (two paths from one column, `Month YYYY`, `header_row` 3,
16 sample rows, every column filled; reader `profile.ddr-board-budget.v1`; file `<slug>.profile.<id>.xlsx`); 3A7's
`reconcile_month record --tenant … --as … --period … --currency … --revenue … --fuel-cost … --source-ref …`; 3B7a's
`build … --by`; the board budget's lines add to Kobo 1,445.00, Kisiwa −65.00 (stated −60.00), Mto 915.00 and the
stated figures to 9,688.00 revenue and 4,995.00 fuel cost.

- **P1 (Medium) Dependencies not on `main`:** `AccountService.tenant_by_slug` is 3A6's (D-3A6.17; today only the store
  has it, `accounts/store.py:37`); `reconcile_month`, `source_profile`, `build_structure_snapshot`, `deep_dive`,
  `record_action` and `build_agreed_actions` do not exist yet. Of these only 3C2's have no spec (R1).
- **P2 (Low) 3A7 role:** `record` needs `commercial.accounts_statement` (3A7 §5); confirm FINANCE_AND_COMMERCIAL_LEAD
  holds it under 3C0a's role table, or S5 exits 2 `PERSON_ROLE_REQUIRED`.
- **P3 (Low) The fuel text depends on 4d unit 3** (`LitreLeafSource` wired in `build_structure_read`) and on 3B7a's
  payload keeping `Missing.note` (3B7a `MISSING` has `note`): both hold by the specs.

## Round 2 (pre-build, after the 21 Nov merges)

Fresh Claude reviewer and pre-flight in one pass, 2026-11-21, on `main` 08f3bf86c (5c units 1-2, DS4, 3A7, 4d, 5b,
ON1, 3C2 unit 1, 0K4b/0K4c/0K4e, SC-1f merged). Read-only; no database opened. Severity as round 1. Each item names
the file:line it rests on and the default that applies if the Architect does not answer.

### Reviewer questions (R)

- **R12 (High, coordinator's call recorded) The rehearsal database's name is outside the authorised names.**
  `spec.md:24`, `spec.md:195`, `rulings.md:10` and `Docs/engineering/operator-deep-dive-runbook.md:33-36,46,132` name
  `assetops_rehearsal_ddr1`; the owner authorises only `*_test` and `<prefix>_audit*` (memory rule; `.ai/RULES.md`
  §7). **Recorded: the coordinator renames it `assetops_rehearsal_ddr1_test`.** Default: fix the class, not the
  instance: the runbook's template becomes `assetops_rehearsal_${REHEARSAL}_test` in every line that names it
  (steps 2, 3's `KEY_DIR`, 4, 6 and the erase step), the example stays `REHEARSAL=ddr1`, and spec §0, §5 and
  D-DDR.1 read `assetops_rehearsal_ddr1_test`. The reviewer checks that no line in the runbook or spec names a
  rehearsal database without the `_test` suffix.
- **R13 (High) G10's screen half cannot pass on `main`: 3C2 unit 2 is not merged.**
  `backend/assetops_backend/deep_dive/composition.py:40` still composes `NotConnectedActions()` ("3C2's unit 2
  replaces this line"); `deep_dive/actions.py:18-22` returns `AgreedActions(False, ())`, so `actions.rows[0]`
  (`spec.md:70`, D-DDR.9) never exists. Default: D-DDR.5 and Q1 (`spec.md:235`) hold as written: DDR's build starts
  after 3C2 unit 2 merges (3C2 `spec.md:33-34`, gate C, is now open). The reviewer checks the build base contains
  `StoreAgreedActions` in `deep_dive/composition.py`.
- **R14 (Medium) §3.4's screen literals predate today's merges.** `spec.md:151-157` quotes the setup gap as "one
  generator and one fuel tank declared in the Site's setup (litres are worked out for one of each)"; `main` renders
  "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)"
  (`i18n/statements/en/vocabulary.py:85`; `backend/tests/test_5c_deep_dive_view.py:48`). 0K4b, 0K4e and SC-1f also
  merged after rev 2. Default: the expectation file's `screen` literals are re-transcribed by hand from 5c's merged
  World B test literals (`test_5c_deep_dive_view.py:46-58,176-177,324`) plus §3.4's listed differences, never from a
  run (W2); every other wording drift found is a mid-build question, not a silent edit.
- **R15 (Medium) Who serves the rehearsed tenant for the owner's 5c walk, and on which ports.** `spec.md:198` says
  the served tenant on the rehearsal database is what the owner walks, but nothing in DDR serves it. 8990/5490 belong
  to the 13 Nov serve and 8991/5491 to WK (`specs/WK-walkthrough-database/rulings.md` D-WK.5), and
  `tools/walk_world.py` serves only walk manifests. Default: DDR adds no serve; the coordinator serves the rehearsal
  database by the 13 Nov shape (uvicorn `lab_app:app`, Vite dev, env built without `ASSETOPS_PSEUDONYM_KEY_DIR` or
  any real-data, entry or upload switch) on 8992/5492, an Architect call logged before §5 runs.
- **R16 (Medium) The owner's one-figure rule on the rehearsed screen.**
  `owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`: two figures for one quantity only where they set up
  something to act on or reconcile. G9 compares the whole `notices`, `tiles`, `bridge`, `cash` and `outcomes`
  (`spec.md:143-146`). Default: the two-figure places allowed are Kisiwa's budget notice (−60.00 against −65.00, a
  reconcile) and plan against actual; the reviewer reads the expectation file's `screen` for any other quantity shown
  twice, and Kobo's stop-70 litres and value read "Not available yet" (no EMS export in this world). A breach is a
  product finding for the Architect, not fixed inside DDR (no product code, `spec.md:27-28`).
- **R17 (Low) G1 reads the pseudonym key, but §2.1 reads only `DATABASE_URL`.** `spec.md:53,61`. Default: the checker
  also reads `ASSETOPS_PSEUDONYM_KEY_DIR` (exit 2 `NO_KEY_DIR` before any read), checks the key through 3A2's
  `PseudonymKeys` port (`commercial/pseudonym.py:126-138`: missing, erased or unusable is a G1 FAIL), and prints no
  path under it and no key content (D-DS4.19's rule).

### Implementer questions (I)

- **I1 (High) `rehearsal_check.py` adds English to the SC-1 package.** `spec.md:55` (`DDR_GATE_FAILED G<n> <text>`)
  and the per-gate `text`; `tools/checks/statement_catalogue.py:35` scans all of `backend/assetops_backend`, and a
  prose literal there is `HAND_BUILT_NEW` (`statement_catalogue.py:426-427`, rule g). D-0K4.19 forbids new baseline
  entries. Default (D-0K4.19 kind 4, text no person on screen reads): each gate's `text` is a code plus facts, e.g.
  `{"gate": "G5", "state": "FAIL", "code": "STATEMENT_MISSING", "facts": {"period": "2026-10"}}`, and stderr is
  `DDR_GATE_FAILED G<n> <CODE>`; exit-2 refusals are codes only. No statement, no baseline or allow-list edit.
- **I2 (High) S11 and G10 need 3C2 unit 2** (R13). `record_action` (`record_action.py:34-40,70`) and
  `build_agreed_actions(url).service.for_tenant(tenant_id)` (`actions/composition.py:220-239`;
  `actions/agreed.py:262`, newest first, takes the tenant's UUID) exist on `main`; the screen does not read them.
  Default: wait for 3C2 unit 2; if it slips past day 9, build S1 to S10 and G1 to G9, and leave G10 and test 1's last
  line as the one open item (Q1).
- **I3 (Medium) The composition returns tuples, not services.** `deep_dive/composition.py:32` returns
  `(DeepDiveRead, dispose)`; `actions/composition.py:220-223,229` returns `AgreedActionsService(service, dispose)`;
  `DeepDiveRead.month` takes a `TenantRef(id, slug, name)` (`deep_dive/read.py:43`;
  `sites/foundation_records.py:49-52`). Default: G9 unpacks `read, dispose = build_deep_dive_read(url)`, builds the
  `TenantRef` and `names` through `ImportedSiteRegistry` (`sites/cutover.py:50,71,90`) as the route does
  (`deep_dive_api.py:49,58`), and disposes every store in `finally`.
- **I4 (Medium) The setup and fuel-text literals** (R14): same evidence; default as R14. Also: `G4`'s Kisiwa check is
  a five-field `TargetCheck("contribution", -60.00, <lines>, "USD", False)` on `main`
  (`test_5c_deep_dive_view.py:313`), not the triple at `spec.md:67`; default: compare `stated`, the lines' sum and
  `agrees` by field name.
- **I5 (Low) Cited names checked and found.** `source_profile admit --tenant --profile --sample --expected --as`
  printing `admitted_by` (`source_profile.py:60-66,124`); `load_emulated_exports` `KEYS`, `<slug>.profile.<id>.xlsx`,
  `EXPORT_PATHS_MIXED`, `PROFILE_NOT_ADMITTED` (`load_emulated_exports.py:50-62,82-85`); `reconcile_month record`
  options and default tolerance 1 in 100 (`reconcile_month.py:48-64`; `structure/reconciliation.py:7,137-140`; the
  latest statement per scope supersedes, `:380-402`); `build_structure_snapshot build|verify` and `BUILT_BY`
  accepting `person:<uuid>` (`build_structure_snapshot.py:50-56`; `structure_snapshot/model.py:24-25`);
  `AccountService.tenant_by_slug` (`accounts/service.py:129`); `pg_harness.empty_tables(engine, roots)`
  (`tests/pg_harness.py:392`, it takes the root tables); `build_workbook` (`tests/fixtures/3a6/make_budget_xlsx.py:72`);
  `tests/fixtures/targets_lakeside.json`; `held_uploads` (`commercial/store.py:64`). Default: none needed; the
  builder names `empty_tables`' roots in the packet.
- **I6 (Low) `portfolio_history` sits beside `latest_portfolio`** in the port, memory store and Postgres adapter
  (`structure_snapshot/store.py:30,69`; `adapters/postgres_structure_snapshot_store.py:90`). It also changes
  `backend/assetops_backend`'s tree, which is part of DS4's L1 key (`tools/world.py:39-40,223-225`), so DDR's merge
  makes the world stale again (WK). Default: as round 1 R11; the coordinator rebuilds (S9) after DDR merges and
  before §5, and WK's run follows DDR's merge, not the other way round.
