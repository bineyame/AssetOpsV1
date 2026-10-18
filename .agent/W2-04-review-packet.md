# W2-04 review packet - cold Site, evidence and unpriced consequence

Task `tasks/W2-04-cold-site-evidence-money.md` (USER_REVIEW_REQUIRED: true, in the later owner W2 walkthrough).
Branch `task/W2-04-cold-site-evidence-money`, worktree `AssetOpsV1-review2`. Final revision: see the last commit
(packet commit on top of `f6f10777`). Binding: `.agent/W2-04-build-spec.md` incl. its ruling sections.

## Outcome delivered

- Phase 1: migration `0023_w2_cold_consequence` (append-only cold consequence revision/evidence/work/attempt,
  scoped FKs, trigger-only work, guarded downgrade); cold consequence worker (advisory lock, one transaction,
  SUCCEEDED/FAILED attempts, overlap group counted once); five selected reads `GET /api/sites/{code}/cold/overview`,
  `/evidence`, `/evidence/analysis`, `/financials`, `/financial-assumptions`. No price, currency or stock value seeded.
- Phase 2: five v69 routes `cold` (5 panels), `cold-evidence` (3), `cold-evidence-analysis` (2), `cold-financials`
  (3), `cold-assumptions` (1), with `expectV69Panels` stocked/empty/refused + planted-panel failure tests.

## Files materially changed (vs merge-base `54b0bece`, excluding `.agent`)

Backend: `analytics/cold_site_reads.py`, `cold_site_api.py`, `adapters/postgres_consequence_store.py`,
`financials/cold_consequence.py`, `financials/cold_recompute.py`, `financials/composition.py`, `main.py`,
`migrations/versions/0023_w2_cold_consequence.py`; tests `test_w204_cold_{consequence,migration,reads,worker}.py`
plus head-revision/constraint-count updates in seven earlier test files (incl. `test_s405_resolver_postgres.py`, Run 9).
Frontend: `sites/coldSiteViews.tsx`, `sites/coldSiteClient.ts`, `sites/w2-cold-site.css`,
`sites/ColdAssessmentViews.tsx`, `sites/assessmentGraphics.tsx`, `shell/{coldSiteRoutes,SiteAnalyticsFrames,
SiteDetailFrame,SiteEvidenceFrame}.tsx`, `App.tsx`, `test/panelStructure.ts`, `sites/__tests__/coldSiteViews.test.tsx`.
Tools: `checks/configuration-persistence.ps1`, `writer_guard_probes.py`, three evidence tools (one-line changes).

## Rulings applied (all from the spec / named decisions; one commit group each)

1. Spec Q1-Q10 (commit 1) and Commit-2 stored codes/screen copy (incl. Q4 open episode: proved low, null high,
   `OPEN_EPISODE_UPPER_UNKNOWN`; worker codes `COLD_BASIS_MISMATCH`, `COLD_RECOMPUTE_FAILED`, `STORE_UNAVAILABLE`,
   `WORK_SCOPE_MISMATCH`).
2. Run-5 Q-R1..Q-R9 and the eight Run-5 reading verdicts (capability details, backup chain selection, last
   accepted fact time, source row order, UNKNOWN-contact sentences, pending money, cutoff, watermark); Q-R9 record
   links stay UNAVAILABLE with `Analysis view not available for this cold record`.
3. Retro rulings Dev 14 (no cold Analysis link until proven; labelled text) and Dev 17 (`Loading / batch` label,
   loading detector).
4. Run-7 ruling: date bar `Selected window ... UTC` / `Selected evidence through ... UTC` (`2a17ef1f`); Evidence chip
   from four row chips (`5781eb4f`); exact source-to-row placement, one-line closed cells, one `Source details`
   (`414ed872`); Analysis three rows + `Show all {N}` + `Record details` + two-sentence claim panel (`48159c02`);
   Overview link/card copy and UTC times (`3a03b439`); Financials one line per cell + `Basis details` (`4c106b60`).
5. Run-8 ruling: `ToLink` null fallback `No linked page for this item`, Cooling note (`f0da723c`); Claim details
   pointer sentence, rule-level IDs removed, `total_count` confirmed, assumptions sentence test (`7372c264`);
   closed-panel compaction - fixed widths 24/17/13/26/20 and 28/9/17/14/16/16, `Sent (UTC)`/`Received (UTC)`,
   short first-cell labels, 6 px padding/gaps, claim disclosure gap -2 px (`e6be9a82`).

## Implementer decisions not covered by a ruling (none were intended; these need Architect confirmation)

- R1. Data sources unbound rows (Transfer switch, Loading / door log) keep the Run-7 copy `No accepted report for
  this role` in the closed What cell instead of the Run-8 labels `Transfer position` / `Door/loading context`.
  Run 8 kept it so a label does not imply an accepted report; the two rulings disagree for unbound rows.
- R2. `w2-cold-site.css:101` `td > * { white-space: nowrap }` (Run 8) to satisfy "Keep each Status/Quality chip on
  one line". See defect D1: with the ruled widths the chips overflow.

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| 0023 upgrade/downgrade, mini-grid rows unchanged, FKs, append-only, unique basis/attempt, trigger-only work | Met - `test_w204_cold_migration.py` |
| Six W2-02 replays via S2 intake through W2-03 with the named expected states | Met - `test_w204_cold_consequence.py` |
| No spoilage/repair amount, null not zero, source-gate/current-money withholding, historical cutoff | Met - consequence/reads tests |
| Cross-tenant refusal, 31-day/limit/cursor/errors, worker failure/retry/idempotence/concurrency | Met - reads/worker tests |
| Rule 8: only `postgres_consequence_store.py` cold INSERTs | Met - probes 129 CAUGHT / 0 MISSED at `4c106b60`; backend code unchanged since |
| `expectV69Panels` per owned route, stocked/empty/refused + planted failure | Met - `coldSiteViews.test.tsx` |
| Side-by-side 1440/390 captures for every route | Met - 18 pairs, 216/216 claims, recaptured after the Run-9 fixes (`.agent/W2-04-evidence`) |
| Panels <= ~1.3x mock at 1440 or stated reason | Met after D2 (Accepted records 1.29) |
| No set/order/title/grid/prominence mismatch | Met per capture tool; D1 closed (no overlap, viewed) |

## App vs mock heights (stocked, 1440, disclosures closed; capture `HEAD_REV`)

| Route | Panel | App | Mock | Ratio |
| --- | --- | --- | --- | --- |
| cold | What happened | 252 | 274 | 0.92 |
| cold | Chamber temperature / Needs attention | 386 | 373 | 1.03 |
| cold | Bounded money consequence / Next step | 185 | 193 | 0.96 |
| cold-evidence | What we can conclude now | 386 | 336 | 1.15 |
| cold-evidence | Data sources / Most useful next evidence (row) | 545 | 438 | 1.24 (target <=569: met) |
| cold-evidence-analysis | Accepted records | 344 | 266 | 1.29 (target <=345: met) |
| cold-evidence-analysis | How a claim limit is set | 191 | 148 | 1.29 (target <=192: met) |
| cold-financials | What happened → money | 300 | 234 | 1.28 |
| cold-financials | Assumptions in use / Not included | 291 | 234 | 1.24 |
| cold-assumptions | Financial assumptions | 315 | 279 | 1.13 |
| temperature (W2-03) | How each limit is set | 225 | 120 | 1.88 - W2-03 follow-up, not this slice |

390: no page overflow on any route (`overflowX 0`). `cold-evidence-stocked-1440-app.png` and
`cold-evidence-analysis-stocked-1440-app.png` viewed: no clipping, overlap or ellipsis in Data sources (headers wrap on two
lines, closed chips Unknown/Not declared/Good/No fact on one line); Record IDs keep their existing 12ch visual shortening.

## Run-9 fix table (Architect D-2026-10-18-w2-04-buildspec, spec section "Run-9 ruling")

| Item | Fix | Where |
| --- | --- | --- |
| D1 | Widths 26/16/16/23/19; headers Source, Contact at window end, Accepted quality, What it provides, Affects (shared CSS shows them uppercase and wraps them here); closed chips Recent/Old/Never/Unknown/Mixed, Not declared, Good/Limited/Mixed/No fact; blanket `td > * nowrap` replaced by nowrap on `.badge` only | `coldSiteViews.tsx`, `w2-cold-site.css` |
| R1 | Unbound and bound-no-fact roles read `No accepted report for this role` (role label only with an accepted fact); Source details keeps `Configured source, no accepted report`; test asserts no `Door/loading context` for a zero-fact bound row | same, `coldSiteViews.test.tsx` |
| R2 | Data sources / next-evidence row measured 545 px (<=569) | capture |
| D2 | Closed Record cell: `Record {short id}` (full id as aria-label) + `No analysis link`; limitation, full id and `Target: Unavailable` moved to Record details; PROVED still uses its exact link. Panel was 370 px after the copy move alone, so records-table line spacing is 1.25 (line spacing only, no text scaling, 6 px spacing kept) -> 344 px | same |

## Known deviations

- D1, D2, R1, R2 are closed. No unruled decision remains; the 1.25 line-height is the only measured lever beyond the
  copy ruling and is within the ruled "no text scaling / keep 6 px spacing" limits - flag for the Reviewer.
- D3. Capture data differ from the mock illustration (seeded excursion replay; rows are Chamber/Ambient/Grid power).


## Checks run (final revision `6177f1dc`; docs-only commit after it)

| Check | Result |
| --- | --- |
| Capture seed (throwaway excursion chain -> W2-03 run -> W2-04 drain, `assetops_w204cap_test`; file deleted) + `tools/w1-fidelity-evidence.mjs`, 18 targets x 2 widths, API 9704 / vite 6104 / CDP 9714 | 216/216 claims passed |
| Full backend, real Postgres, `-n 2 --dist loadfile --no-loadscope-reorder --junitxml`, `assetops_w204_test`, keep-awake | 2823 passed, wall 1720 s; JUnit cases=2823 skipped=0 failed=0 |
| Host suite `pytest host/tests` (run after, serially) | 708 passed, wall 637 s |
| Full frontend `vitest` | 86 files / 2225 passed (one `npm.cmd test` run hit 1 failure under load; the rerun and the sites/shell run were clean) |
| `tools/check-all.ps1` | All 10 guards passed |

The earlier `test_s405_resolver_postgres` failure was fixed in `f6f10777` and passes in this run.

## Residual risk

- `SOURCE_GATE_CHANGED` worker path has no positive test (every replay batch links before acceptance).
- `cold_consequence_room` depends on W2-03 writing Foundation IDs into `analytic_run.foundation_revision_ids`.
- Shared files with W2-05a: `configuration-persistence.ps1`, `writer_guard_probes.py`; merge-base is behind main.
- W2-03 accepted-record links open the cold Analysis list by ID (not focused); not a Q-R9 proof.

## User-review focus

D1 overlap on Evidence › Overview Data sources; D2 Accepted records height; R1 unbound-row copy; financials stay
unpriced with `Not included` explicit; no Action/Incident/repair implied.
