# S4-05b review packet - registered producers, Finding reads and owner walkthrough

Task: `tasks/S4-05b-producers-reads-walkthrough.md` (size M, two phases). Branch
`task/S4-05b-producers-reads-walkthrough` (worktree `AssetOpsV1-review2`), unmerged. USER_REVIEW_REQUIRED: true -
owner W1 source-copy checkpoint (`.agent/S4-05b-owner-walkthrough.md`) before merge. Rulings:
`.agent/architect-S4-05b-answers.md` (D-2026-10-16-s405b-label). Phase-1 review: `.agent/S4-05b-phase-1-review.md`
(ACCEPT, 3 Lows; L1/L2 fixed in `fbdc7066`, L3 closed by the walkthrough run and layout evidence below).

## Outcome delivered

- Producers publish each exact batch before upload (P01/P02 authored, `tools/s4_finding_cases.py` `publish_authored`);
  the Lab Commit registers a registered run's sealed Stage before release (`runs/registered_release.py`); a Stage
  not wholly sealed refuses with `SOURCE_PUBLICATION_REFUSED` / `STAGE_NOT_ATTESTABLE`, nothing released.
- Every product read (Finding, Evidence, consequence, Financials bridge, S5 Overview, recommendation, Action detail)
  takes source state from the stored exact-revision resolver. `demonstration_label.py` is deleted; no reader left.
- Money gate: `MIXED_OR_UNKNOWN_SOURCE` withholds a current amount in Financials, consequence and the S5 Overview,
  whatever the CURRENT PRICED / LR eligibility, with every reason at once; history stays audit-only with its own
  source state.
- UI labels and statements exactly per the ruling table, visible without a disclosure (also at 390 px and to
  assistive technology); IDs and reasons in the source-record disclosure; no vocabulary exemption.
- Pilot schedule install gate always requires `I-attested-real-source-provenance`.
- `tools/s405_provenance_walkthrough.py prepare|links|serve|drop` (owner, old-host and mixed cases) and
  `tools/s405-provenance-evidence.mjs` (browser claims at 1440/390); S5-01 packet amended (shared contract item 5).

## Files materially changed

Backend: `evidence/provenance_read.py`, `financials/consequence_read.py`, `finding_api.py`, `site_overview/read.py`,
`actions/service.py`, `actions/composition.py`, `analytics/finding_read.py`, `runs/registered_release.py`,
`host/lab_execution.py`, `host/lab_app.py`, `contracts/.../lab_projection.py`; deleted `demonstration_label.py`.
Frontend: `sites/sourceProvenance.tsx` (new), `FindingConsequence.tsx`, `SiteFinding.tsx`, `SiteFindingEvidence.tsx`,
`SiteWindowOverview.tsx`, `SiteAction.tsx`, `SiteRecommendation.tsx`, clients. Tools: `s405_provenance_walkthrough.py`,
`s405-provenance-evidence.mjs`, `s4_finding_cases.py`, `s402b_power_cases.py`, `s402c_late_power_walkthrough.py`,
`s5_overview_walkthrough.py`, `s402b-fuel-cost-evidence.mjs`, `schedule-install-gate.py`. Packets:
`tasks/S5-01-site-overview.md` (amendment). Fixture `backend/tests/fixtures/s6_action_api_contract.json` regenerated.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| P1 producers publish before upload; failure stops upload | Met | phase 1; walkthrough owner case: P01 6 / P02 6 publications, every cited and power ID bound |
| P1 ordinary run registered via Lab Commit before gateway upload | Met | walkthrough ordinary day: REGISTERED_SIMULATION, 85 publications, 1 recorded run |
| P1 every P01 cited/power ID published; ordinary contextual ID -> MIXED | Met | `test_s4_power_demo_case_postgres` (s405b cases); mixed case below |
| P1 same-day unbound and old host -> UNKNOWN, never backfilled | Met | old case: 0 publications, UNKNOWN, `NO_POSITIVE_BINDING` |
| Partly sealed Stage refused whole, visible in Lab | Met | L1 tests; host `test_an_unreadable_stage_refuses_commit_and_releases_nothing`; `runCommitPanel.test.tsx` "keeps a source publication refusal visible" |
| P2 money gate in Financials, consequence, S5 Overview; simultaneous reasons; historical audit-only | Met | `test_s4_assumption_read_api`, `test_s5_overview_read`, `test_lr01_money_eligibility_postgres`, `test_s5_overview_postgres`; walkthrough |
| P2 Actions read pinned origin revision; unresolved -> Source unverified | Met | `test_s6_action_store_postgres`, `siteAction.test.tsx` |
| P2 S5-01 packet amended (S4-05b merges second) | Met | `tasks/S5-01-site-overview.md` lines 34/39/52 |
| P2 install gate requires attested-real node | Met | `test_s4_schedule_install_gate` (open, missing, resolved) |
| P2 walkthrough prepare/links/serve/drop, guards, exact IDs/JSON | Met, with deviation D1 | run below |
| Labels per ruling; visible at 1440/390 and to AT; vocabulary scan | Met | `sourceProvenance.test.tsx`; layout evidence 178/178 |
| Owner copy approval | Pending | owner checkpoint |

## Walkthrough run (end to end: prepare at `edecf2ba`, links/serve/layout/drop at `b32e6c6b`)

`.venv/Scripts/python.exe tools/s405_provenance_walkthrough.py prepare`: **0 failed checks in 455 s** (owner 0, old 0,
mixed 0; 15 s405 checks plus the reused S5/LR-01 checks). Then `links`, `serve --case owner|old|mixed` (API 8935,
web 5435), layout evidence per case, then `drop` (3 DBs dropped, 3 work folders removed).

| Case / day | Finding / revision | Money | Finding source | Consequence source | Publications |
| --- | --- | --- | --- | --- | --- |
| owner P01 2026-10-23 | `18ddd37b` / `5cf04684` | PRICED 0.00-15.82 USD | AUTHORED_DEMONSTRATION | AUTHORED_DEMONSTRATION | 6 |
| owner P02 2026-10-24 | `3631a672` / `7fac575b` | WITHHELD_GENERATOR_SERIES | AUTHORED_DEMONSTRATION | AUTHORED_DEMONSTRATION | 6 (disjoint from P01) |
| owner ordinary 2026-10-02 | `3b0f1488` / `f61efdfd` | QUANTITY_UNAVAILABLE | REGISTERED_SIMULATION | REGISTERED_SIMULATION | 85, 1 run |
| old P01 2026-10-23 | `2224815c` / `744f8fbb` | MIXED_OR_UNKNOWN_SOURCE | UNKNOWN | UNKNOWN | 0 (144 IDs unbound) |
| mixed P01 2026-10-23 | `99789892` / `6ff597f1` | MIXED_OR_UNKNOWN_SOURCE | MIXED | MIXED | 5 (48 IDs unbound) |

The S5 Overview agreed on every day (same money state and source). IDs are from this run; `prepare` makes new ones.

## Layout evidence

`node tools/s405-provenance-evidence.mjs http://localhost:5435 <case> var/s405_evidence` against each served case:
owner **98/98**, old **40/40**, mixed **40/40** claims passed. Per page (Overview, Finding, Evidence, Financials) and
width (1440x1000, 390x900): notice rendered (non-empty set measured), the ruling's label for the stored state, label
in the viewport / not in a closed disclosure / not aria-hidden, "No current cost is shown." on MIXED/UNKNOWN, no
page-level horizontal overflow; v6.9 mock `#/financials` renders at both widths. Screenshots in `var/s405_evidence/`
(gitignored, local only).

## Checks run (final revision)

- `tools/check-all.ps1`: All 9 guards passed (includes the dependency registry checker and check-architecture /
  check-agent-workflow).
- `npx.cmd tsc --noEmit`: exit 0. `npm.cmd test`: 67 files, **1588 passed**, 149 s, no timeout file.
- `runCommitPanel.test.tsx` alone: 20 passed.
- Full backend suite at `64c6f6bd` (code-final; later commits are docs only), PowerShell, private base DB
  `assetops_s405b_test`, `var/sites/*.yaml` copied from main and removed afterwards, keep-awake running, 3.9 GB free:
  `python -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -p no:cacheprovider --junitxml=<scratchpad>/full-junit.xml`.
  **2408 passed, 30 warnings in 1130 s (18:50 wall, cap 25 min)**; JUnit tests=2408 failures=0 errors=0 skipped=0.
- Focused Postgres/host checks during phase 2: see `.agent/S4-05b-phase-2-handoff.md` (132+3 passed; mutation of
  `permits_current_money` -> 5 failures, reverted).

## Known deviations

- D1: the packet asks for the unbound same-day batch and the mixed case inside the owner DB. P01 exists once per spec
  day, so the walkthrough builds them as separate private DBs on the same P01 day: `assetops_s405_old` (old producer,
  every batch unbound: the same-day unbound and old-host case together) and `assetops_s405_mixed` (one context
  device unbound). `serve --case` switches the API on 8935; the web server stays up. Default names take an optional
  `--suffix`.
- D2: the Financials screenshot can catch the "Fuel cost versions" panel still loading; claims do not depend on it.

## Residual risk

- `MoneyInputs.provenance_resolved` defaults to True for S5 unit tests; production always passes it.
- Ordinary unpublished Findings now show Source unverified and no current amount everywhere (intended).
- The Action contract fixture grew (~840 KB) because each response carries the full provenance block.
- Consequence history resolves provenance per row (2 queries x up to 50 rows).

## User-review focus

The four labels and sentences, their placement near the result and next to any amount, and the plain "Source record"
disclosure (W1 copy checkpoint). Merge waits for the owner record.
