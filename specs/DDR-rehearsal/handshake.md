# DDR handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4). Empty: no round yet.

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
