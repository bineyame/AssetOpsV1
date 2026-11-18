# W5-01a C2 review (Cooling page)

Reviewer: fresh independent Claude reviewer, 2026-10-22. Branch `task/W5-01a-cold-selected-depth`, code diff `b6c74709..2812d7aa -- frontend backend tools` (main merges excluded; C2 commits `a4288c66`, `06c8c3cc`, `af17bcf2`, `2812d7aa`).

## Verdict: ACCEPT

No High or Medium findings.

## What was checked

- **File list.** The 12 changed files are all on the C2 card: the three new files, `App.tsx`, `SiteAnalyticsFrames.tsx`, `ColdAssessmentViews.tsx`, `coldSiteViews.tsx`, `shell/coldSiteRoutes.tsx` (Q-C2-1), `ui/V69Layout.tsx` (one `cooling` description key), `coldRoutes.test.tsx` (Q-C2-5 edit only, matching the ruling line by line), and the two navigation guard files. `operatorSiteRoutes.ts` is unchanged, which is allowed because `sitePerformanceHref(id, "cooling")` already gives the route. The backend is unchanged.
- **Literals.** I compared each one against the ledger, the C2 state matrix, Q-C2-2/3/4 and the shared capture section, and all match exactly:
  - the breadcrumb `Sites › {Site} › Performance › Cooling`, with Temperature and Backup still ending at `Performance`;
  - the subtitle `Performance · recovery under comparable conditions`;
  - the three state rows: status, `Confidence:`, subtitle and fourth note;
  - the four card values and notes;
  - the `Recovery curves` description, its `Step`/`Time (UTC)`/`Evidence` columns and its empty sentence;
  - the `Factor`/`Evidence`/`Status` columns (no `Match`) and every Evidence cell wording, including `doorDuration`;
  - the bounded notice, the two `Next best evidence` items, and the four state notices;
  - the loading `<p className="prose">`, the unreachable and malformed sentences, the `Cold depth unavailable` heading with the server `code message`, and the `Retry` button.
- **DTO.** `keysExactly` checks key sets without regard to order at the top level and in `window`, `selection`, `links`, `cooling`, each point and each context row. Value sets are enforced:
  - `cold-depth-1` and the five selection states;
  - `LIMITED`/`CONTRADICTORY`/`UNKNOWN`;
  - the four time and duration fields always null, and `CONTEXT_MISSING`;
  - five labels in ledger order, and `Observed`/`Unknown`;
  - `[]` when the state is Unknown, and an integer `duration_seconds` only on an observed door row.

  A malformed 200 becomes `unavailable` and then the refusal block. Health checks only the envelope, as the card allows (C3 adds the rest).
- **Labels.** `coolingCardLabels(cooling.policy_high_deg_c)` inserts the value as given, and a null value gives `back to policy`. Both cases are tested on the page.
- **No svg.** `ColdCooling.tsx` has no svg and both tables use `DataTable`. The `cooling_panels` test asserts there is no `svg`, and the shell-overflow guard passes.
- **Navigation guard and rail fixtures.** `$expectedTabs` drops one `Cooling`. A new positive check requires both `data-performance-subtab="cooling"` and `<ColdCooling`, with the exact failure message. The old fixture is replaced by the two ruled negative fixtures, and both pass inside `check-architecture`.
- **Wiring.** The Cooling view skips the three W2 reads, because `useRead` takes a null loader. `coldUiHref` maps `cooling`, `links.health` stays unmapped, and `Inspect recovery basis →` and `Open Backup →` go through `coldUiHref`, with a null link rendered as text.

## Checks run (this review)

- `npx.cmd vitest run --minWorkers=1 --maxWorkers=2 src/sites/__tests__/coldDepth.test.tsx src/sites/__tests__/coldRoutes.test.tsx src/sites/__tests__/coldSiteViews.test.tsx`: 3 files, 127 passed (coldDepth 25).
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1`: all 11 guards passed. These include Architecture seams, which runs the rail fixtures and the shell-overflow check, and Navigation truthfulness.
- Not run: the full frontend suite, the production build, and the backend (C2 changes no backend code). The captures were not reproduced; I reviewed them as images and as `evidence.json`.

## Mock comparison (1440 and 390)

`cooling-limited` and `cooling-pending` against the v69 `cooling` mock, at both widths:
- **Order matches.** Breadcrumb → Site h1 → description → Site tabs → Performance subtabs (Temperature / Cooling / Backup) → status bar with action → four cards → `Recovery curves` and `Context normalization` side by side (stacked at 390) → bounded notice → `Next best evidence` with two numbered items.
- **Prominence matches.** At 390 the cards wrap into two columns.
- **Additions** are the ruled selected-window bar above the status bar, and the amber state notice directly below the status bar on non-CURRENT states.
- **Deviations** are only the ruled ones: the chart is replaced by a table, `Match` becomes `Status`, and badges are neutral.

`evidence.json` records, for every capture:
- `scrollWidth <= clientWidth`;
- 0 ellipsized elements;
- panel titles equal to the mock;
- block heights within the cooling caps.

The 422 refused capture shows the refusal block and hides the requested window bar.

## Findings

- **Low L1 (not blocking; outside C2 files).** `.agent/W5-01a-C2-evidence/cooling-refused-390-app.png`: the mobile shell header stretches into a tall dark band (about 280 px) on a short page. This is shell layout (`AppShell`/topbar grid), not C2 code, and the implementer already flagged it. Track it for the W1/W6 UI pass, or check it against an existing short refused page at 390.
- **Low L2 (not blocking).** `ColdCooling.tsx:254` treats every 422 as `invalid-window`, so the requested date line is hidden for every 422. That includes a future-`known_at` 422, where the window itself is valid. This matches the existing `refusalText` precedent in `ColdAssessmentViews.tsx:140`, so it is consistent rather than a regression.
- **Info.** The Next best evidence body text (`Keep load, door, …`) is drawn in the shared `.v69-attention__item p` `--text-secondary` colour, which looks bluish in the captures. It is a `<p>`, not a link, so it complies with "plain text"; the colour comes from the shared primitive.

## Residual risk

- The frontend full suite and the build were not rerun here (cite the implementer's runs).
- The captures were taken at `06c8c3cc`. The only later change is the Q-C2-5 test edit, so the product code shown in the captures is the code under review.
