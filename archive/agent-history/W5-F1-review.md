# W5-F1 review: D3 corrections R22, R37, R38

Reviewer: fresh independent Claude (Opus), 2026-10-23. Branch `task/W5-F1-d3-corrections` at `2552fd65`, diff `main...task/W5-F1-d3-corrections`.
Spec `.agent/W5-F1-build-spec.md`; register R22/R37/R38; handoff `.agent/W5-F1-phase-handoff.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The two Low items below do not block the merge.

## Acceptance checks

- **Every changed file is on a card.** F1-1 covers `SiteHealthFrames.tsx`, `ColdFoundationViews.tsx`, `SiteHealth.tsx`, `coldHealthDepth`, `coldFoundation` and `siteHealthBoundary` tests. F1-2 covers `coldSiteViews` and `coldRoutes` tests. F1-3 covers `coldSiteViews.tsx`, `coldSiteViews` test and `tools/w5f1-d3-evidence.mjs`. The remaining changes are `.agent/` evidence, the handoff and the register status. `ColdAssessmentViews.tsx` is on the F1-2 card but is correctly unchanged, because the row was already in mock order; the dry-read and handoff say so. There is no backend, CSS or guard change.
- **Cold Health ends at Condition and evidence.** The COLDCHAIN branch mounts only `ColdHealthDepth`. `SiteHealthSources` is removed and there are no dead references; the non-cold `SiteHealth` and its private `SourcesPanel` are intact. Tests cover the title list `["Condition and evidence"]`, cards then panel then notice in order, nothing panel-shaped after the notice, and no `/source-health` or `/battery` request in CURRENT, UNKNOWN and refused (`coldHealthDepth.test.tsx`, `siteHealthBoundary.test.tsx:364`). The mini-grid Data sources panel is still asserted (`siteHealthBoundary.test.tsx:358`).
- **The Foundation link has the right target.** `ColdFoundationViews.tsx:646` links to `${evidenceHref}#cold-site-sources-heading`, which is `/sites/COLD-001/evidence#cold-site-sources-heading` in the test. Following the link in the test lands on `/sites/COLD-001/evidence`, and the element `#cold-site-sources-heading` there reads "Data sources · data quality, not equipment condition". The browser capture confirms the href and landing URL at 1440 and 390, and the target panel is visible in `foundation-to-evidence-390-app.png`.
- **Excursion context rows are in mock order.** The tests (`coldSiteViews.test.tsx`, `coldRoutes.test.tsx`) assert exactly seven labels, one `Loading / batch` with value `Not established` between Door opening and Defrost, no "Matched", and no rows on a refusal. In the browser, the stocked and empty states at both widths gave `Excursion window, Upper policy limit, Peak observed, Power outage, Door opening, Loading / batch, Defrost`.
- **Record cells.** `coldSiteViews.tsx:1139-1144` renders one unconditional `REC {evidence_id}` and "Record page unavailable" per row, with no anchor. A test row set to `PROVED` with a self-link still renders no anchor. The tests also check six headings, unique full IDs that share a prefix, and an unchanged Record details disclosure. The served read returned `UNAVAILABLE` with 0 links. In the browser, every record cell had 0 anchors, a full ID and no clipping.
- **The producer `tools/w5f1-d3-evidence.mjs`** is on the F1-3 card and is spec-mandated tooling. It refuses an output directory outside `.agent/W5-F1-evidence/` and requests the real reads before navigating. It settles on route markers, never on `/Loading /`. It uses the shared `widthGuard` and stops only the Chrome it started. It exits nonzero on title, order, link, clip, overflow or response failures. It is acceptable.

## Excursion seed case

**Acceptable, no ruling needed.** The spec says to use "the ordinary W2-02 cold replay ... through `opened`/`run`" and names the event window `2026-10-06T19:00-20:05Z` without naming a case. `excursion` is an existing W2-02 fixture case already used in `test_w203_cold_replay_postgres.py`. It is the only case that produces the Excursion context and accepted records for that window: the served reads returned CURRENT and 93 accepted records. The builder fitted the fixture to the spec's stated window and did not design anything new. Optionally, the Architect can name the case in the spec so a recapture is reproducible (see Residual risk).

## Side-by-side with v69 (run2, 1440 and 390)

- **cold-health:** the app and mock both show three condition cards and then Condition and evidence, with nothing after it except the retained amber condition notice. There is no Data sources panel. At 390 both stack cards 2+1, and the table fits without page overflow.
- **cold-performance (`#/temperature`):** the three panels are in the same order, and the Excursion context rows match the mock sequence, including Loading / batch · Not established. The "How this was worked out" disclosures and the missing "Open Incident" link were already on main and are outside this slice.
- **cold-evidence-analysis:** the six columns and both panels match. In the Record column the mock's `Open record ↗` is replaced by the labelled `REC {id}` and "Record page unavailable", which is the R38 resolution. At 390 the Record column sits inside the existing horizontal table scroller and is not clipped. The paginator ("Show all 93 accepted records") and Record details were already on main.

## Findings

- **L1 (Low, cleanup):** `frontend/src/sites/ColdFoundationViews.tsx:152` still declares `healthHref`, and `SiteFoundationFrame.tsx:147` still passes it, but no cold view reads it any more. Not an acceptance gap; remove it in a later cleanup.
- **L2 (Low, register note for the Architect):** the v69 cold Gateway status action reads `Health › Data sources →` and points to `#/cold-health` (`screens.js:143,164`). The app now reads `Evidence › Data sources →`. The spec mandates this literal and R22's reason records the redirect, so the builder made no choice of its own. However, the changed link text has no `MOCK DEVIATION` code comment and no row of its own. The Architect should confirm that R22 covers the label text, or add a D2 note, so the owner walkthrough index lists it.

## Checks run

- `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on `coldFoundation`, `coldHealthDepth`, `coldRoutes`, `coldSiteViews` and `siteHealthBoundary`: **5 files, 184 tests passed** (22.8 s). It ran in this worktree; the esbuild sandbox denial did not occur.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- **Not rerun (per dispatch):** the full frontend suite, `npm run build`, `check-all.ps1` and the browser capture. I cite the implementer's figures: vitest 113 files / 2697 passed, build OK, and `check-all` 11/11 at `200f97ca`. Capture run2 was at `8e7dd87e`. The commits after `8e7dd87e` change only `.agent/` files, so the source under review is identical to the source measured.

## Residual risk

- The capture DB was seeded by a throwaway test that was deleted, so run2 cannot be reproduced from the repository alone. The handoff records the method (`opened("excursion", chain)` + `run`).
- React Router does not scroll to a `#fragment` on a client-side navigation. The link resolves to an existing target, which is what the spec requires, but it may not scroll the panel into view at 390. Check this at the owner walkthrough.
