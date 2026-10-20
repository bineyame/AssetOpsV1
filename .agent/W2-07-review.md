# W2-07 independent review (EV Site evidence and money)

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/W2-07-ev-site-evidence-money`, head
`1ec71f7a`, diffed against `main`. Read-only except this file.

## Verdict: REVISE

The backend is sound and matches the spec: the money vectors, 0026, R7, R8, and the shared q4 selector all check out.
Four Medium items block the merge. Three are in the UI and copy layer, and one is in the capture evidence. None is
structural, and each is a small fix on the branch.

## Findings

### Medium

**M1. The captures do not show the priced (mock) money state.**
`.agent/W2-07-evidence/seed.py:17` publishes with the test helper's default validity:
`publish(...)` → `backend/tests/test_w207_ev_money_postgres.py:64`. It does not use the spec's golden tariff, which
is valid `[2026-10-06T08:00Z, 09:00Z)` (`golden_tariff`, q1 R2, `GOLDEN_FROM/TO` at `:614`). The live browser state
is therefore `UNPRICED/TARIFF_MISSING` on every route. The mock depicts an estimate on four of the five routes:
`$36.00` card, bridge row, tariff/currency rows and the tariff assumption row.

Taking the five screens in turn:
- **Panel order and titles:** these are adequately evidenced. All 20 pairs match titles and order, and every closed
  height is at or under 1.28x.
- **Priced layout:** this is not evidenced in a real browser. That covers the `KES x.xx gross tariff estimate` money
  panel, the scenario bridge row (`15.000 kWh × 0.27775 KES/kWh`, `Scenario`, `Metered with complete coverage`,
  `Sessions ↗`), the `Tariff` / `Currency` value rows and the R2 `publication_note`.
- **Copy in the priced state:**
  - `tariffText` (`frontend/src/sites/EvSiteViews.tsx:1063`) renders `· ${t.basis}`. With the real store value it
    shows `0.27775 KES/kWh · AUTHORED_ESTIMATE`.
  - jsdom hides this because its fixture uses the literal basis `Authored test tariff`.

Concrete failure: the owner opens the walkthrough at the interrupted window and sees a raw enum in the tariff row.
The estimated bridge row's height at 1440 or 390 has also never been measured against the 371/304 ceilings.

Fix:
1. Seed with `golden_tariff` (valid 08:00-09:00, which covers the interrupted case's four pre-abort intervals).
   This gives `ESTIMATED 15.000 × 0.27775 = 4.16625000`, displayed as `KES 4.17`.
2. Recapture the four money-bearing routes at 1440 and 390, and update the height table.
3. Map `basis` to plain words, or get an Architect ruling that the raw `{basis}` is acceptable.

**M2. Display rounding is half-up; the spec says half-even.**
`frontend/src/sites/EvSiteViews.tsx:151-160` (`money2`) contradicts the build spec's concrete-artifact closure §3:
"The UI rounds to two minor units **half even**". No later ruling changes this. The builder listed it as a Run 9
reading, which makes it an unruled implementer decision.

Failure: amount `8.325` (for example `30.000 × 0.2775`) displays `KES 8.33` where the spec requires `KES 8.32`.

The test at `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx:440` uses `8.335`, which does not tell the two
modes apart, so the defect is untested.

Fix: implement half-even (banker's rounding on the third digit with remainder check), and add a tie case such as
`money2("8.325") === "8.32"`. Alternatively, get an Architect ruling for half-up.

**M3. The Analysis table shows raw system enums where the mock shows plain words.**
`backend/assetops_backend/ev_site_reads.py:650` builds `source_label` as `{display_name} · {public role code}`.
`:652` passes the raw measurement value through as `value_display`.

What renders (capture `ev-evidence-analysis-interrupted-1440-app.png`):
- `Connector c1 · connector_status`, value `AUTHORIZING state`.
- `Connector c1 · session_event`.

What the mock (`screens.js:215`) and the spec's own wire illustration (`Connector 1 · session start`) show:
`Connector 2 · session` and `Connector 2 · energy`.

This breaks the build spec's copy-ledger rule "No UI string is built from a raw enum except by these mappings". It is
the first column of the main Analysis table, on every row.

Fix: map the public role and the status/state values to plain labels (`session`, `energy`, `status`,
`site import`, and so on). Do this either in the read's `source_label` / `value_display` or in the view, and pin the
labels in `ev_evidence_tabs_and_record_limit`.

**M4. The R2 two-clock sentence is not asserted, and it is missing from the Financials basis details.**
q1 R2 says that `financial_tabs_and_price_gate` "must assert the later-publication sentence".

The test (`evSiteMoneyRoutes.test.tsx:384-443`) never does: its fixture sets `publication_note: null` (`:216`).

The sentence renders only on the Assumptions screen, and there as a visible closed note
(`EvSiteViews.tsx:1305`), not inside a details disclosure. The Financials Basis or Assumption details disclosure
(`:1180-1200`, `:1246-1258`) never shows it. On Financials, a priced scenario built from a tariff published after
the evidence cutoff therefore never says that the price was not known at `known_at`. R2 states: "The read must
never say that this tariff was known at the evidence `known_at`."

Fix: render `publication_note` in the Financials Assumption details, and put a non-null note in the test fixture and
assert it on both routes. Optionally, move it into `Assumption details` on the Assumptions route as R2 places it.

### Low

- **L1. Two copy choices need an Architect ruling.**
  - **Null-consequence card:** the Financials `Gross tariff estimate` card, the bridge and `consequenceWord` show
    `Unpriced` for a null consequence (`EvSiteViews.tsx:1070,1110`). That covers UNKNOWN (no assessment) and pending
    with no prior revision, where `/ev` says `No gross tariff scenario assessed` and R8 names that empty copy. The two
    routes therefore show inconsistent wording for the same state.
  - **Evidence aggregate rule:** this rule is unspecified (`EvSiteViews.tsx:253`). The chip aggregates seven
    capabilities, while the strip counts four (`4 capabilities · 2 full · 2 limited`). A Site whose four visible rows
    are all Full can still read `Evidence limited` because of SITE_POWER or POWER_CONSTRAINT.
- **L2. Next-evidence ranking skips the spec's "independent diagnostic/request/limit" rank.**
  `ev_site_reads.py:620-633` emits TERMINAL, METER, STATUS, SITE_IMPORT, TARIFF, BILLING. It never emits a
  requested/allocated-power gap before tariff, even when POWER_CONSTRAINT is missing those roles. This is defensible
  given W2-05a r2 (no declared load manager), but it is unruled.
- **L3. Same-instant chronology order is arbitrary.** In the interrupted case, FAULT and ABORT share
  `08:16:00Z`. The `(source_time, evidence_id)` sort is spec-compliant, but the strip shows `Session aborted` before
  `Connector fault`, which invites a reversed causal reading. A kind tie-break (START, FAULT, ABORT, END) would fix
  it. The chronology code is around `EvSiteViews.tsx:448`.
- **L4. The downgrade test deletes rows despite the spec's "No delete or cascade clears them for the test".**
  To reach a "genuinely empty" downgrade, the test deletes the tariff and work rows under replica role
  (`remove_money`, `test_w207_ev_money_postgres.py:82`, used at `:222`, `:578`). The refusal cases are still proved
  first, so the risk is low. An empty downgrade taken before the tariff publish (work count is already 0 at `:215`)
  would meet the letter of the spec.
- **L5. The capture revision is not stated.** `evidence.json` records revision `e6de374f`, not the final
  `5a26b74b`. The later commit is a pure component move, so the pixels should be unchanged, but the packet should
  state that.

## Builder readings (packet "Builder readings")

| Reading | Classification |
| --- | --- |
| Run 5: `source_class` / `source_gate` | Covered, q4 #1 |
| Run 5: tariff fields and links only for ESTIMATED; null quantity for WITHHELD/INCOMPLETE; UNPRICED keeps kWh | Covered, q4 #2 |
| Run 5: contradiction predicates (CONTRADICTORY, METER_OVERLAP, shared ID, connector overlap) | Covered, R5/R6 |
| Run 5: empty SUCCEEDED attempt | Covered, spec line 27/78 |
| Run 5: window `[08:00, 09:05)` | Covered, q4 #3 |
| Run 6: wire additions | Covered, q5 R5 |
| Run 7: schedule flag, contact keys, coverage unit, demotion, limitation append | Covered, q6 |
| Run 8: enabled connector = `ev-connector-enabled=ENABLED` | Covered in substance by q6 R1 |
| Run 9: evidence aggregate rule | **Needs ruling** (L1) |
| Run 9: four-row claim mapping | Covered, spec slot table |
| Run 9: Next step links (Sessions, Financials) | Covered |
| Run 9: chronology (use ≠ EXCLUDED; `End record missing` from INCOMPLETE) | Covered by q5 copy/source ledger |
| Run 9: chart reads every Analysis page | Covered, q5 |
| Run 9: explanatory rows only when `findings.count > 0` | Covered |
| Run 9: Delivered energy = `complete_kwh` | Covered |
| Run 9: strip count = stored consequence | Covered |
| Run 9: null consequence card = `Unpriced` | **Needs ruling** (L1) |
| Run 9: half-up `money2` | **Contradicts spec** (M2) |
| Run 9: Assumptions has no status strip | Covered by mock authority |
| Run 9: static SLD entry | Covered |

## Spec checks

- **Money vectors:** `test_w207_ev_money_postgres.py:617-623` pins `30.000 / 8.33250000`, `15.000 / 4.16625000`,
  `10.000 / 2.77750000`, missing-meter `UNPRICED / INCOMPLETE_ENERGY`, late-record revision 2 at `8.33250000`, and
  contradictory `WITHHELD / CONTRADICTORY_EVIDENCE` with null amounts. `ev_money.derive` follows the R5 precedence.
  Amount is an exact Decimal product with no rounding in storage or hashes.
- **0026:** the body is the spec literal: CHECK names asserted, the EV-only positive CHECK, five tables with scoped
  FKs/uniques, the state/arithmetic CHECK, append-only triggers, the one-success partial unique, and the exact scoped
  `ON CONFLICT` target. `ev_consequence_on_accepted` is the R7 literal body, and the source-gate trigger stays
  immediate. The downgrade guard covers the tariff, assignment and all five tables, then restores the diesel-only
  CHECKs.
- **R8:** `EvUnit.pending` is the literal predicate. A pending item rolls back and appends FAILED `PENDING_RECOMPUTE`
  in a fresh transaction under the work lock, with no revision or links. Retry follows `retry_due_at`.
  `test_pending_retry_settles_without_new_assessment_revision` covers it.
- **Five reads:** one `EvGate` (W2-06's, refactored without behaviour change) and one repeatable-read
  `EvReadService.open_on` envelope. `_select` implements the q4 order: UNKNOWN → no consequence, HISTORICAL/PENDING →
  history only, CURRENT → derive and take the matching basis by `revision_no DESC, id DESC`, else a read-only
  `STALE_BASIS` guard.
- **Panels:** titles and order match `v69-rendered-panels.json` on all five routes at both viewports. Closed heights
  are at most 1.28x.
- **`from` / `to` / `known_at`:** preserved in links and tabs.

## Checks run by the reviewer

- Focused backend, on private DB `w207r_test` (dropped afterwards): `test_w207_ev_money.py`,
  `test_w207_ev_money_postgres.py`, `test_w207_ev_site_reads_postgres.py` → 29 passed, 0 failed, 610 s at `1ec71f7a`.
- Frontend: `npx.cmd vitest run src/sites/__tests__/siteFinancials.test.tsx src/sites/__tests__/evSiteMoneyRoutes.test.tsx`
  → 2 files, 88 passed (83 + 5). `siteFinancials` passed on this single rerun, which is consistent with the builder's
  load-flake explanation. It is not proven to be a flake, but there is no evidence of a W2-07 regression.
- `npx.cmd tsc --noEmit` → exit 0.
- `tools/check-architecture.ps1` → passed. `tools/check-agent-workflow.ps1` → passed.

Not rerun: the full backend suite (3264 passed / 0 skipped at `5a26b74b`), the host suite, the production build, and
the browser captures. These are cited from the packet. The full-suite revision `5a26b74b` differs from head
`1ec71f7a` only by the packet commit.

## Residual risk

- Neither the EV nor the cold consequence worker is scheduled by any runtime host. This is the existing W2-04
  pattern. Until a scheduler runs `EvConsequenceWorker.run`, a live tariff publication leaves the reads at
  `WITHHELD / STALE_BASIS`.
- Two `process_one` calls on different work items for the same window can race on the basis/revision unique keys.
  The snapshot is taken before the advisory lock, so the loser records `EV_RECOMPUTE_FAILED` and replays on retry.
  `run`'s Site claim prevents this for scheduled runs.
