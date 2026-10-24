# W5-04 V2a handoff — EV Site Work Actions tab (pure fixtures)

Branch `task/W5-04b-ev-work-ui`, based on main `6927bb33` (merged K4/K5 and rulings 1-52). Ruling 39 lets V2a be built
before V1b merges, using pure fixtures shaped from the as-built V1b index wire
(`task/W5-04a-ev-work-backend:backend/assetops_backend/work/domain_action_index.py` `_select`/`index`). This handoff
makes **no producer-backed claim**, and V2a may not merge on an unreviewed wire. Open interpretations are in
`.agent/W5-04-V2a-questions.md`.

## Units and commits

| Commit | Content |
| --- | --- |
| `7f03100e` | Code. `domainActionClient.ts` parses EV rows as domain Actions (ruling 46) and picks the EV network/shape sentences per Site type (ruling 44). `evWorkPresentation.ts` holds the EV literals. `SiteWorkActions.tsx` generalises the K2 tab to `DomainSiteWorkActions`/`DomainWorkWindow` through a `DomainWorkPresentation` object (cold and EV). `SiteAnalyticsFrames.tsx` dispatches on Site type: `SiteWorkFrame`, `WorkSubrow`/`useWorkCounts` and the `SiteWorkCasesFrame` subrow. `operatorSiteRoutes.ts` adds `domainWorkQuery`, with `coldWorkQuery` kept as an alias. `SiteFoundationChange.tsx` adds the EV subtitle (R78). `w1f4-changes-work.css` uses `domain-work-*` selectors. |
| `f7158a08` | Tests. `evWorkFixtures.ts` and `evWorkActions.test.tsx` (17). EV blocks added to `w1f4ChangesWorkStructure`, `operatorSiteTabs` and `operatorRouteFrames`. Cold dual-naming regression in `coldWorkActions`. Mini-grid domain-attribute absence in `siteWorkActions`. `panelStructure.ts` `SCREEN_LEADING['ev-work']`. |
| (this) | `.agent/W5-04-V2a-questions.md` and this handoff. |

## Behaviour delivered (EV_CHARGING Site, `/sites/{site}/work`)

- **Layout.** v69 `ev-work` structure: breadcrumb, Site header with `EV charging operations at this site.` (R78),
  Work tab, subtabs, page-local `Window` (R112, R77 UTC labels), scope strip, the one `Actions at this site` panel
  (six mock columns), then the blue domain notice (R03).
- **Strip.** `Scoped to {shortName(display_name)} · 1 action|{n} actions` (R79, R111), with
  `EV Actions recorded at this site` and the plain gap `Global Actions does not include EV Actions yet.` (R04).
  Loading and refusal show `— actions`.
- **Row cells.**
  - The EV Action code and title are **plain text** (R113, ruling 46). No href to `/actions/{id}` is emitted.
  - Source is plain `Finding {id8}`, with the revision and the unavailable note in the `Finding version` disclosure
    (R74/R75).
  - Owner, or `Not assigned`. UTC due date, or `Not set`. Amber `Open`. The server `criterion_summary`, or
    `No success criterion declared`.
- **Due subtitle.** `Due dates are not yet set` appears only when every row has `all_due_dates_unset` (R76).
- **W1 rows on the EV Site.** They keep the W1 link, state and fallbacks (pre-flight 28).
- **Currentness notice.** Placed between the strip and the panel (R80), blue or amber (R104). No notice on `CURRENT`.
- **Successful zero.** The exact mock zero copy.
- **Refusals.** 403/503/409 and network/shape failures show an untitled state with `EV work unavailable`, the server
  message and `Retry`.
- **Paging.** Four-row fold with `Show all {n} Actions` (R108), plus the cursor pager.
- **Window.** The default is the last seven complete UTC days (R-9). Apply keeps `known_at` and drops the cursor.
  Subtab hrefs carry `from,to,known_at`.
- **Attributes.** EV elements carry only `data-domain-work-*` attributes, `domain-work-*` classes and `domain-work-*`
  disclosure names (ruling 45).

## Cold behaviour

Cold output keeps every K2 `data-cold-work*` attribute, `cold-work-*` class, disclosure name, literal and two-argument
`getIndex` call. Cold elements additionally carry the `data-domain-work-*` attributes and `domain-work-*` classes
(ruling 45). The existing cold suites pass unchanged: `coldWorkActions`, `coldWorkCases`, `siteWorkActions`,
`w1f4ChangesWorkStructure`, `DataTable`, `operatorSiteTabs`, `operatorRouteFrames` and `domainActionVerification`
(200/200 before the new tests were added). A new cold test proves both naming sets are present and that the read keeps
two arguments. The detail parser, `DomainActionVerification.tsx` and `ColdDomainActionShell` are untouched (V4a).

## Counts and checks (final revision)

- `npx tsc --noEmit`: clean.
- Targeted vitest (`--minWorkers=1 --maxWorkers=2`): `evWorkActions` 17/17, and 152/152 across `coldWorkActions`,
  `siteWorkActions`, `operatorSiteTabs`, `w1f4ChangesWorkStructure` and `evWorkActions`. `operatorRouteFrames` 20/20.
- Full vitest (`--minWorkers=1 --maxWorkers=2`, revision `f7158a08`): **125 files, 2904 tests passed**, 7m10s.
- `npx vite build`: built (only the existing chunk-size warning).
- `tools/check-all.ps1`: **All 11 guards passed**, including architecture seams, agent workflow, navigation
  truthfulness, missing-claim and screen ledger.
- Non-vacuity proofs: each mutation was applied on committed code, run against `evWorkActions`, then reverted with
  `git checkout`.

  | Mutation | Result |
  | --- | --- |
  | EV `legacyCold: true` | 2 failed |
  | EV `domainActionLink: true` | 2 failed |
  | EV branch removed from `isRow` | 1 failed |
  | `SCREEN_LEADING['ev-work']` removed | 1 failed |

- Layout evidence: **not run**. Captures belong to V2b and need a reviewed V1b manifest, so 1440/390 heights, the
  table scroll and the ruling 25/50 caps are unverified in V2a.
- No Postgres was used, no server was started, and no PID was left.

## Judgment calls (also in the questions file)

1. EV case tabs get only the domain subrow (counts and cutoff). The Window and `windowForm=false` are left to V3a, to
   avoid a duplicate form (Q1).
2. The EV subtitle edit is in `SiteFoundationChange.tsx`, which is not on the card (Q2).
3. The R75 unavailable note sits inside the disclosure, using the K4 literal (Q3).
4. There is no separate Site-zone indicator. The labels are the ruling 14 UTC labels (Q4).
5. `tools/w504-ev-work-evidence.mjs` was not created. Captures are deferred to V2b (Q5).
6. CSS selectors were renamed to `domain-work-*`, and cold elements carry both class sets (Q6).
7. `coldWorkQuery`/`ColdWorkQueryScope` stay as aliases of `domainWorkQuery`, so there is still one route grammar.
8. `getIndex(siteCode, scope, siteType?)` gained an optional third argument that selects only the fallback sentences.
   The cold caller keeps its two-argument call byte-for-byte.
9. The register needed no edits. R77/R78/R112/R113 already carried the ruling 48 wording on main, and all IDs used in
   code comments exist.

## Shared plumbing touched

Yes, limited:
- `domainActionClient.ts` (union parser and the optional `siteType` argument).
- `SiteWorkActions.tsx` (the cold component was generalised).
- `SiteAnalyticsFrames.tsx` (Work dispatch, subrow and counts).
- `operatorSiteRoutes.ts` (`domainWorkQuery` alias).
- `SiteFoundationChange.tsx` (header subtitle branch).
- `w1f4-changes-work.css` (selector rename).
- `test/panelStructure.ts` (one leading entry).

There are no backend, App route or registry changes.

## Next

- Before V2a merges, V1b review and the Architect's answers to the questions are needed.
- V2b: producer-backed captures at 1440/390 using the reviewed `positive`/`mock-zero` manifests, the ruling 25/50 caps
  and the evidence tool.
- V3a: EV case cells, `data-domain-cases`, the EV Window plus `windowForm=false`.
- V4a: the EV detail route and live `links.action` href (closing R113), plus the shell generalisation.

## Fix round (review ACCEPT with Lows; rulings 53–66), commit `35b01c25`

Branch head before the fix round was `de65b15e`, which merged main with rulings 53–66. Only frontend code and tests
changed. Every test was run with `--minWorkers=1 --maxWorkers=2`.

### Fixes

| Item | Change and proof |
| --- | --- |
| **Low-1** | `workAttrs` with no value now renders the cold `data-cold-work-*` attributes as `="true"`, byte-for-byte as in K2, while the domain name renders `""`. The notice keeps K2's explicit `""`. Every base attribute form was checked against the new calls. The new assertions are in `coldWorkActions`. Non-vacuous: reverting the default fails 1 test. |
| **Low-2** | `EV_WORK_PRESENTATION.domainActionLink = EV_ACTION_LINK_LIVE`, so one switch now controls R113. Non-vacuous: flipping it fails 2 tests in `evWorkActions`. |
| **Low-3** | Three new EV tests: Next pins the response `known_at` and First drops the cursor; a 409 `WORK_BASIS_CHANGED` restarts page one keeping `known_at`; the ruling 57 interim case tab has no `data-domain-work-window` and exactly one form, the W4 form. Per the fix list, `siteDetailRoute` stays a regression run with no EV vector. |
| **Low-4 / Q1–Q6** | Rulings 57–66 confirm all six calls. R75 and R77 were already amended on main (ruling 65), so there were no register edits. |
| **Ruling 53** | The row shape is unchanged. The fixtures doc records the intent-pin semantics and adds `evPinUnavailableRow()` (`origin.href: null`). A test shows the Source exactly as supplied, pinned (CURRENT) or unavailable (UNKNOWN), with no list/detail disagreement copy. |

### Checks

- `tsc --noEmit`: clean.
- Targeted vitest: 10 files, 247/247. The files are `evWorkActions`, `coldWorkActions`, `coldWorkCases`,
  `siteWorkActions`, `w1f4ChangesWorkStructure`, `operatorSiteTabs`, `operatorRouteFrames`, `siteDetailRoute`,
  `domainActionVerification` and `DataTable`.
- `check-all`: **All 11 guards passed** (on `35b01c25`).
