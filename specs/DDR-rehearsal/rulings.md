# DDR rulings

Architect (Claude), 2026-11-20; rev 2 the same day (D-DDR.7 to D-DDR.10, handshake answers below). Each ruling is
indexed in `.ai/decisions/index-rulings-13.md`.

## D-DDR.1 The rehearsal is the runbook run as written, with a checker of what each step leaves

- **Ruling.** DDR is twelve runbook steps (spec §1) and `rehearsal_check`, which reads the records each step leaves
  and fails at the first missing one. The automated test runs the same steps; the coordinator then runs them on
  `assetops_rehearsal_ddr1` with an agent that has only the runbook.
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

## D-DDR.5 DDR waits for 3C2

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
