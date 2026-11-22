# DDR rulings

Architect (Claude), 2026-11-20; rev 2 the same day (D-DDR.7 to D-DDR.10, handshake answers below); rev 4 on 2026-11-22 (D-DDR.16, owner-away row 76); rev 3 on
2026-11-21 (D-DDR.11 to D-DDR.15, "Handshake answers (round 2)"; owner-away delegation
`owner/owner-away-architect-stands-in-2026-11-21b.md`). Each ruling is indexed in `.ai/decisions/index-rulings-13.md`
(D-DDR.1 to D-DDR.10) or `.ai/decisions/index-rulings-23.md` (D-DDR.11 on).

## D-DDR.1 The rehearsal is the runbook run as written, with a checker of what each step leaves

- **Ruling.** DDR is twelve runbook steps (spec §1) and `rehearsal_check`, which reads the records each step leaves
  and fails at the first missing one. The automated test runs the same steps; the coordinator then runs them on
  `assetops_rehearsal_ddr1_test` (D-DDR.12) with an agent that has only the runbook.
- **Why.** "Proven end to end" means a person can do it from the runbook, not that a test harness can; the checker
  makes a skipped or bypassed step visible after the fact.

## D-DDR.2 The unseen shape is the operator's board budget, and it replaces the emulated budget

- **Ruling.** The budget arrives as an XLSX board pack (title rows, header on row 3, month as "October 2026",
  thousands separators, negatives in parentheses), read by a profile admitted by command; the emulated
  `budget.csv` is removed from the folder before loading.
- **Why.** One source system per source type per Site (D-3A6.5) forbids two budgets for a Site; the board budget
  carries Kisiwa's −60.00 contribution line, so the disagreement the screen must show (D-5B.10) arrives through the
  real path; a profile is data, so the run proves "no code change".

## D-DDR.3 Each gate reads its own step's records, never another gate's output

- **Ruling.** G1 to G10 each query the store their step writes (tenant and grants, profiles, uploads, records and
  targets, statements, snapshots, Actions) and the screen read; the order of gates follows the steps.
- **Why.** A check that trusts an earlier check's result cannot see that the earlier step was bypassed (test 4: records
  written without an upload fail G3).

## D-DDR.4 The rehearsal shows "not yet reconciled" before it shows "reconciled"

- **Ruling.** The finance lead's first figures differ by 105.00 of fuel (beyond the 51.00 allowed); the month is
  prepared and shown; the corrected figures follow and the month is prepared again.
- **Why.** Risk 2 of the plan: most operators' first comparison fails; the screen must say so plainly, and the owner
  should rehearse that conversation (3A7).

## D-DDR.5 DDR waits for 3C2 (amended by D-DDR.14: DDR builds beside 3C2 unit 2 and is reviewed on a base holding it)

- **Ruling.** S11 and G10 need 3C2's `record_action` and `build_agreed_actions` (3C2 spec, rev 1, written in this
  round; 5c spec §4.3); DDR builds after 3C2's two units merge.
- **Why.** RC9 makes the agreed change part of the deep-dive; a rehearsal that skips it would not prove the path.

## D-DDR.6 One read is added to the snapshot store: the month's portfolio rows by "as of"

- **Ruling.** `portfolio_history(tenant_id, period)` in the port, the memory store and the Postgres adapter; nothing
  else in 3B7a changes.
- **Why.** G6 must see that a snapshot was prepared between the two statements; `latest_portfolio` cannot show an
  earlier one.

## D-DDR.7 G9 compares the screen's figures and words, never its clock

- **Ruling.** G9 compares a named key set of the body with the expectation file and ignores the keys that carry the
  build's instant or the reader's clock (`as_of`, `as_of_text`, the status line's first sentence, `nav`, `state_text`)
  and the Action (`actions`, G10's). It asserts `state` SERVED, `fresh.current` true and `fresh.untracked_text` null.
- **Why.** The rehearsal builds at its own instant; a gate that compares a fixed time passes only on one day
  (handshake R2). The figures, words and named gaps are what the owner walks; they do not depend on the clock.

## D-DDR.8 Each gate checks who did its step

- **Ruling.** G2 checks the profile was admitted by Wanjiru; G6 and G8 that the snapshots were built by
  `person:<Wanjiru's id>`; G3 (already) the submitter and acceptor; G5 and G7 the finance lead; G10 the executive and
  the owner.
- **Why.** A step done by another path (a profile written to the store, a snapshot built by a service) leaves the
  same records but not the same person; the rehearsal proves a person can do it from the runbook (handshake R3).

## D-DDR.9 G10 reads 3C2's store, then the screen's first row

- **Ruling.** G10 passes when `build_agreed_actions(url).service.for_tenant(tenant)` holds, first, an Action titled as
  S11, created by Amina, owned by Peter, due 2026-12-15, at KOBO-001 on `candidate_l`, and the screen body's
  `actions.rows[0].title` is that title.
- **Why.** D-DDR.3: the gate reads the store its step writes; the screen check proves 5c shows it (RC9).

## D-DDR.10 Each test case starts from empty tables; the rehearsal runs whole only where it must

- **Ruling.** Every case empties the tables (`pg_harness.empty_tables`, the harness's reset) and uses fresh temporary
  folders; one pooled database per run. Test 1 runs the twelve steps once and checks the checker after every step
  (the progress test, folded in). The skips run only their own case. While building, the builder runs test 1 alone;
  tests 3 and 4 run once before review; the packet records the module's wall time, and the cap is twice it.
- **Why.** `lakeside-power` and its emails can be onboarded once per database (handshake R4); the owner's test
  policy keeps full runs for milestones. "No S11" is test 1's state after S10, so it needs no run of its own.

## D-DDR.11 The checker speaks in codes and facts, never English (I1)

- **Ruling.** Each gate line is `{"gate", "step", "state", "code", "facts"}`; a FAIL's code and facts are spec §2.4's;
  stderr is `DDR_GATE_FAILED G<n> <CODE>`; an exit-2 refusal is its code alone. No statement is written, and no SC-1
  baseline or allow-list entry is added. Facts hold identifiers, codes, plain-string figures, UTC times and JSON paths,
  never a screen string.
- **Why.** `rehearsal_check.py` sits in SC-1's scanned package (`tools/checks/statement_catalogue.py:35`), where a prose
  literal is `HAND_BUILT_NEW`; D-0K4.19 forbids new baseline entries. Its output is read by the coordinator and the
  tests, never by a person on screen (D-0K4.19 kind 4), so codes carry everything it must say.

## D-DDR.12 Every rehearsal database is `assetops_rehearsal_${REHEARSAL}_test` (R12; the coordinator's call, as a class)

- **Ruling.** The runbook template, its key folder (`/opt/assetecon/keys/assetops_rehearsal_${REHEARSAL}_test`), spec
  §0 and §5, D-DDR.1, both runbook copies and ON1's runbook test value use the `_test` name; the example stays
  `REHEARSAL=ddr1`, so the rehearsal runs on `assetops_rehearsal_ddr1_test`.
- **Sweep (W6), `git grep assetops_rehearsal` on the answers branch:** `Docs/engineering/operator-deep-dive-runbook.md`
  lines 34, 36, 46, 67, 79, 95, 114, 132; `specs/ON1-operator-tenant/runbook.md` lines 35, 37, 47, 68, 80, 96, 115,
  133; `backend/tests/test_on1_served_tenant.py:90`; this spec's §0 and §5 and D-DDR.1 (fixed here). The first three
  are DDR's build edits (spec §6); `specs/ON1-operator-tenant/rulings.md:191` is ON1's history and stays.
- **Why.** The owner authorises only `*_test` and `<prefix>_audit*` databases on the test container. One template
  fixes every future rehearsal, not this one.

## D-DDR.13 The coordinator serves the rehearsal database on 8992 and 5492 for the owner's walk (R15; owner-level)

- **Ruling.** Spec §5.2: the coordinator serves it in the 13 Nov shape (uvicorn `lab_app:app` from `host/`, Vite dev),
  with WK §3.5's environment list built by `env -i`, on API 8992 and web 5492, from a detached worktree
  `/opt/assetecon/AssetOpsV1-ddrserve` at the 5c unit 3 branch's reviewed head (else `main`) holding 3C2 unit 2 and the
  rehearsal database's migrations. No key folder, no real-data, entry, upload or gateway switch. It is stopped by
  checked PID before the erase. DDR adds no serve code. Logged as owner-away row 65.
- **Why.** The owner walks 5c's unmerged screen on the rehearsed tenant (5c §9). 8990/5490 belong to the 13 Nov serve
  and 8991/5491 to WK (D-WK.5), so the next free pair keeps the three serves apart. WK §3.5's list is already reviewed,
  so the hand-run serve repeats a checked environment rather than a new one.
- **Reversible.** Stop the two PIDs; serve on other ports by the same steps; no code depends on the ports.

## D-DDR.14 DDR builds now, beside 3C2 unit 2; it is reviewed and merged on a base holding unit 2 (R13, I2; amends D-DDR.5)

- **Ruling.** 3C2 unit 2 is already specified (3C2 spec §3 and test 9, 0.25 unit, handshake round 1 covered it; gate C
  is open since 5c units 1 and 2 merged). It is pulled first on day 14 (D-3C2.16). DDR's branch starts from `main`
  now: S1 to S10, G1 to G9 and tests 3 to 8 first; G10 and test 1's S11 and S12 lines are written to the spec and run
  once `main` holds unit 2 and is merged in. The review starts only from such a base. G10 is not left open, and Q1's
  slip clause is retired.
- **Why.** The owner wants the deep-dive rehearsed before the 5c walkthrough. Unit 2 is one class and one composition
  line, so waiting for it costs hours. Dropping G10 would leave RC9 (the agreed change as an Action) unproved, and
  building in parallel keeps the fortnight's DDR on time.

## D-DDR.15 The runbook admits the layout before receiving the exports, and ON1's runbook test grows with it (Architect pre-flight A1)

- **Ruling.** Spec §6: new section 6 (admit), then 7 (write, replace, load: three blocks), 8 to 11, and 12 (erase).
  Both runbook copies are edited identically. `backend/tests/test_on1_served_tenant.py`'s section 3 table gets the
  twelve-command `EXPECTED`, five more parsers and five more `VALUES`, with `KEY_DIR` on the `_test` name.
- **Why.** Rev 2 put the admission after the section that writes and loads the exports in one block. An analyst with
  only the runbook would then load before admitting (`PROFILE_NOT_ADMITTED`) and could not swap the budget file.
  ON1's test 3 requires exactly the listed commands, a parser for each program, every declared variable, and identical
  copies (D-ON1.13, D-ON1.19). Without the edit, DDR's runbook breaks ON1's tests at review, which would be a
  mid-build question.

## D-DDR.16 §5.2's API environment carries the two cursor keys (D-WK.15; amends D-DDR.13; owner-away row 76)

- **Ruling.** §5.2 step 3 adds `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` and `ASSETOPS_WORK_CURSOR_KEY_HEX`, each a
  fresh 64-hex value per serve, generated in the shell and passed only through `env -i`. They are never written to a
  file or the log.
- **Why.** The rule is D-WK.15's, from the reviewed list this serve copies. Without the keys the estate routes answer
  503 `ESTATE_STORE_UNAVAILABLE`. The coordinator restarted the DDR serve this way on 2026-11-22, and those routes
  answer 200.
- **Reversible.** Remove the two names from step 3.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `task/4d-5c-DDR-handshake` 8ce960a64. Every answer is folded into `spec.md`
rev 2. Each gate named here has a plant in `reviewer-guide.md` rev 2 that fails it.

### Reviewer

- **R1 (High).** Accepted. 3C2 now has its spec (`specs/3C2-agreed-change-action/`, 1.5 units): the store G10 reads
  (`agreed_action`, read through `build_agreed_actions`), the role rules (only the executive agrees, D-3C2.2; Peter as
  Site manager of KOBO-001 owns a Kobo change), which Actions count (agreed Actions only; the S6-01a finding Actions
  never, D-3C2.1, D-5C.17) and the state words ("Open", "Overdue"). G10 per D-DDR.9. "No S11 → G10 fails" is test 1's
  check after S10 (D-DDR.10). Gate: P9 (G10 passes on any Action of the tenant) fails test 1's S10 line.
- **R2 (High).** Accepted: D-DDR.7; §3.4 names the compared keys and the ignored ones. Gate: P10 (G9 compares
  `as_of_text`) fails test 1 (the run builds at its own instant, never 2026-11-20T08:00Z) and test 8(c).
- **R3 (Medium).** Accepted: D-DDR.8. Test 3 gains "no S8 → G7"; test 4 gains "S6 with `--by service:shortcut` → G6";
  test 8 checks G2, G6 and G8 against injected reads naming another person. Gates: P11 (G2 ignores the admitter),
  P12 (G6/G8 ignore the builder).
- **R4 (Medium).** Accepted: D-DDR.10.
- **R5 (Medium).** Accepted. G4 also checks per Site the cash leaves (`collected` 3800.00, 3180.00, 1890.00;
  `in_transit` 0.00, 0.00, 150.00 for Kisiwa, Kobo, Mto: 3A3 E3) and that `diesel_price` is valued with every source
  `commercial:` (3A3 E4 gives litres on every fuel invoice), which is what keeps `untracked_text` null. Outstanding is
  5b's arithmetic, compared by G9. Gate: P13 (G4 without the cash leaves) fails test 8(d) (injected reads with
  Kobo's `collected` 3000.00).
- **R6 (Medium).** Accepted: G6's upper bound applies only when a later statement exists.
- **R7 (Low).** Accepted: tests 1 and 3 assert ten lines on every checker run.
- **R8 (Low).** Names come from the Foundation's imported Sites of the tenant, the route's own read
  (`ImportedSiteRegistry(<the tenant's Foundation service>).imported_sites()`), so they equal the screen's.
- **R9 (Low).** Accepted: the XLSX bytes are committed; `make_board_budget.py` is byte-stable (fixed ZipInfo times
  and order); test 7 regenerates and compares bytes and the SHA-256. Gate: P14 (a timestamp from the clock) fails
  test 7.
- **R10 (Low).** Accepted: S2's output line holds `admitted_by` (Wanjiru's id); runbook section 7 says to copy it,
  and section 9 uses it in `--by person:<id>`.
- **R11 (Low).** Accepted: runbook section 9 says "after every accepted import, every statement and every deploy";
  snapshots built before DDR merges read "the way they are worked out has changed" and are rebuilt (S9) before the
  walkthrough; the coordinator re-runs S9 after any deploy before day 11.

### Implementer pre-flight

- **P1 (Medium).** DDR builds after 3A6 (`tenant_by_slug`, D-3A6.17), 3A7, 3B7a, 4d, 5c and 3C2 (both units) merge;
  3C2's spec exists now.
- **P2 (Low).** Confirmed: 3A7 gives `commercial.accounts_statement` to FINANCE_AND_COMMERCIAL_LEAD; Joseph holds it.
- **P3 (Low).** Confirmed: the fuel text needs 4d unit 3 and 3B7a keeping `Missing.note`; both hold by their specs.

## Handshake answers (round 2)

Architect (Claude), 2026-11-21, on `task/DDR-WK-handshake-answers` (questions at 99b1d8279; `main` 83419e876 merged in).
Folded into `spec.md` rev 3 and `reviewer-guide.md` rev 3.

### Reviewer

- **R12 (High).** Accepted as a class: D-DDR.12 (sweep listed there).
- **R13 (High).** D-DDR.14: 3C2 unit 2 first on day 14, DDR built beside it, reviewed on a base holding
  `StoreAgreedActions` (the reviewer checks it with `git grep`).
- **R14 (Medium).** Accepted: §3.4 now quotes `main`'s wording ("a generator and a fuel tank declared in the Site's
  setup (litres are worked out for each)") and says the literals are transcribed by hand from 5c's merged World B test
  literals. Any other drift is a mid-build question.
- **R15 (Medium).** D-DDR.13, spec §5.2 (owner-away row 65).
- **R16 (Medium).** Accepted: D-WK.12 (one ruling for both units; owner-away row 66). The allowed pairs are Kisiwa's
  budget notice, plan against actual, and the statement against the records only while they do not match. Kobo's
  stop-70 litres and value read "Not available yet". A breach is a product finding for the Architect.
- **R17 (Low).** Accepted: `NO_KEY_DIR` (exit 2), G1 through `PseudonymKeys` (`KEY_STATE`), no key path or content
  printed; test 8(f).

### Implementer

- **I1 (High).** D-DDR.11; spec §2.4's code table; test 8(g).
- **I2 (High).** D-DDR.14 (the slip clause is retired).
- **I3 (Medium).** Accepted: G9 unpacks and disposes, builds `TenantRef` and `names` through `ImportedSiteRegistry` as
  the route does.
- **I4 (Medium).** Accepted: the literals as R14; G4 compares `TargetCheck` by field name (`factor_id`, `stated`,
  `computed`, `currency`, `agrees`).
- **I5 (Low).** No change; the packet names `empty_tables`' roots.
- **I6 (Low).** Order reversed by D-WK.14: WK's run (steps 1 to 5) comes before DDR's merge, because WK copies the world
  at its commit and DDR adds nothing served. DDR's merge makes the world stale for the *next* WK, which is expected
  (D-WK.6). The rehearsal (§5.1) runs after DDR's merge, so its S9 is already after the deploy.

### Architect pre-flight

- **A1 (High).** D-DDR.15: the runbook order and ON1's runbook test (spec §6, test 9).
