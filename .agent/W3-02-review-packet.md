# W3-02 review packet (estate Evidence and Financials roots)

Task: W3-02, `tasks/W3-02-estate-evidence-money-basis.md`; contract `.agent/W3-02-build-spec.md` (rulings c1-c4b).
Branch `task/W3-02-estate-evidence-money-basis` (head `5fe9d4b2`); final-review fixes on `task/W3-02-fix-final`.
USER_REVIEW: UI slice; hold the merge for the owner walkthrough (W1 rule).

## Commits (one Lane B/Lane A pair per phase)
1 backend Evidence read/API `c9e19695` `71c00d59` `9efa3914` `33b9711e` (fix r1). 2 Evidence page `d9f898e7`, shell/registry
`9e05d970`, fixes `cd98969a` `ce75d9c4`, c2b `39afe950`, c2c `93b065e8`, fix r1 `e45f4219`. 3 Financials read/API `54625bdc`,
c3-q2 `181f62c6`, c2d `f9ef4034`, two-Site fixture `6f065647`/`f1e49236`, r1 fixes `f4242856`. 4 Financials page `97d00521`,
shell/registry/links `d59dad32` `36fcf8ac` `e3d18027`, c4 fixes `d2519fd3`, c4b `5fe9d4b2`. Final-review fix: this branch.
Merges of `main` and handoff-only commits omitted.

## Files materially changed
- Backend: `estate/evidence_money.py`, Evidence and Financials routers, `ev_site_reads.py` (`capabilities_on`,
  `claim_limit_on`, `select_consequence_on`), test-only `ev-complete-lab-002` fixture, Postgres tests `test_w302_*`.
- Frontend: `estate/EstateEvidence.tsx`, `EstateFinancials.tsx`, `estateFinancialsWords.ts`, clients, `estateEvidence.css`,
  `estateFinancials.css`; shared: `ui/PageHeader.tsx` (eyebrow), `primitives.css`, rail (Evidence and Financials live),
  `settled.ts` loading regex, shell route frames, registry/ledger entries, two navigation guard fixtures.
- Evidence tooling `.agent/W3-02-evidence/` (serve/capture scripts, mock measurements, 1440/390 PNG and JSON).

## Acceptance (task exit criteria)
| Criterion | Status / proof |
| --- | --- |
| Evidence: every authorized Site's capabilities, coverage/currentness, Site destinations; gaps only from typed roles; no mock Action | Met. Commit 1-2 Postgres + `estateEvidence.test.tsx`; reviews below ACCEPT |
| Financials: exact selected consequence revisions, bounded/unpriced/withheld values, lineage; totals only in complete comparable groups; no cross-category inference | Met. Commit 3 reads, `rendersComparableAndExcludedReasons`, two-Site COMPARABLE fixture (c3b), `PARTITION_INELIGIBLE` plain words; no estate total |
| Window and `known_at` retained; missing/pending/conflicting Sites visible; unknown never zero | Met. Notes (empty scope, no selection, partial, L5 prior mini-grid, conflict, historical); link-follow tests (`test_w302_financials_links_postgres.py`) |
| Positive, empty, pending, mixed-source, mixed-currency, overlapping-basis variants | Met in tests; captures cover positive and partial (pending); mini-grid line absent (limitation below) |
| Mock layout (panel set/order/titles, 1440/390 maxima) | Met after the final fix; see captures |

## Builder readings and rulings
All pending readings (c1-q1..q3, c2-q1..q8, c3-q1..q3, c3b-q1/q2, c4-q1..q4) are resolved by the build-spec rulings c1,
c2/c2b, c3/c3b, c4/c4b; `.agent/W3-02-pending-rulings.md` now marks each with its section. Key readings: EV
`historical_label` and `METER_GAP` input (c1-q1/q2), refusal copy for unnamed W3-01 codes (c2-q2), gap `site_names`
(c2-q1), raw cold role code replaced by plain sentences (c2-q7), second EV Site admitted test-only for
`ev-complete-lab-002` (c3b), Aggregation prose at 12px/1.8 with one closed results summary (c4/c4b). Per-commit detail:
`.agent/W3-02-phase-handoff.md`.

## Independent reviews
| Unit | Verdict |
| --- | --- |
| spec review / closure checks | `W3-02-spec-review.md`, `closure-check*.md`: closed before build |
| 0a | ACCEPT (`W3-02-0a-review.md`) |
| 0b | REVISE then REVISE (one mechanical deletion) (`0b-review`, `0b-rereview`), fixed |
| 0c | REVISE then ACCEPT (`0c-review`, `0c-rereview`) |
| commit 1 | REVISE then ACCEPT, two Lows (`commit1-review`, `commit1-rereview`) |
| commit 2 | REVISE then ACCEPT (`commit2-review`, `commit2-rereview`) |
| commit 3 | REVISE then ACCEPT (`commit3-review`, `commit3-rereview`) |
| commit 4 / whole slice | REVISE at `5fe9d4b2` (H1 narrow register scroll, M1 packet, 4 Lows); this fix round closes them |

## Accepted limitations
- c4-q3: "Three Sites are in scope; two have selected consequence lines. The mini-grid has no selected consequence revision
  for this window, so no mini-grid amount appears in the register. The two-row register height is not a three-row
  mock-density proof; the 293/448 px register maxima still apply." (also in both capture JSONs as `limitation`.) The
  three-row fit is now asserted from measured row heights (below).
- Notice has no info icon and the status chip size differs slightly (shared primitives, W1 UI pass).
- Registry and ledger entries `I-estate-money-root`, `globalfinancials:1-2` stay `gap` (c4-q2).

## Final-review fixes (this round)
- H1: at 390 the table is 800 px wide (inside its own horizontal scroll) with `max-height: 300px`; rows measure 78 px, header
  30, so header + 3 rows = 264 <= 300 and no vertical scroll (register positive 288, partial 332; three-row worst case
  partial 332 - 185 + 264 = 411 <= 448). Test asserts header + 3 x max row <= cap, scrollH <= clientH, and the three-row
  register <= 448 from `app-financials-*.json` (`maxH`, `headH`, `rowHs` now captured).
- M1: this packet. L1 rulings marked. L2: summary text exposed, full sentence appended visually hidden (name = visible text +
  sentence). L3: `Basis details` replaces `Basis: N revisions`. L4: PageHeader comment corrected.

## Captures (private `w302z_test`, dropped; servers stopped by port)
`financials-{positive,partial}-{1440,390}[-open]-app.png`, `app-financials-*.json`. Positive 390 viewed: two rows,
no clipped row, no raw code. Heights (max): 1440 status 46 (68), register 256/280 (293), notice 43 (66), aggregation 121
(123); 390 status 69 (95), register 288/332 (448), notice 61 (102), aggregation 186 (187). Document width = client width at
both widths. Mock rectangles for both widths are in the JSON and `.agent/W3-02-mock-measurements.md`.
`tools/layout-evidence.mjs`: not run; the custom CDP script `capture-financials.mjs` supplied the measurements.

## Checks
Final fix revision: focused `src/estate src/ui` 101 passed; full frontend 102 files / 2435 passed, tsc clean, build ok,
check-all 11/11. Full real-Postgres suite: run by the coordinator on review2 at `5fe9d4b2`
(backend unchanged since; JUnit cases/skipped/failed and wall time to be cited by the coordinator from that run).

## Residual risk
Mock comparison is by measured rectangles, not pixel diff. A third register note plus three rows is bounded by the test's
computed 411 px estimate, not by a captured three-row state. Only positive and partial states are captured.
