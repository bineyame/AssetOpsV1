> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 8 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## W2-01 - cold Foundation, readiness and configured topology (built, in_review)

Branch `task/W2-01-cold-foundation` (base main `8e0af014`; design `archive/agent-history/W2-technical-design-cold.md` section 3 A-I, panel map section 6). Packet `archive/agent-history/W2-01-review-packet.md`; phase-1 handoff `archive/agent-history/W2-01-phase-1-handoff.md`.

- Backend (phase 1): `0021_w2_cold_config` no-op anchor; cold component types, node roles, media, `event`/`degC` units and the 13 `cold-*` properties in `sites/models.py`/`foundation_parsing.py`; immutable `cold-roles-1` (14 roles, EVENT value kind, role-specific state ENUMs, 300 s periodic cadence) in `sites/binding_roles.py`; `sites/cold_foundation.py` validator (runs on import and every revision) and `cold_foundation_document`; `GET /api/sites/{code}/cold/foundation?at=` (`cold_foundation_api.py`); `FoundationService.publish_topology`; W2-00 Low 2 folded (`ChannelMapping.role`, ledger `MAPPING_INCOMPATIBLE` on role drift, `BINDING_CHANNEL_ROLE_MISMATCH`). Fixtures `backend/tests/fixtures/w2/cold-00{1,2}.yaml` + `backend/conversions/cold-00{1,2}-bindings.json`.
- Frontend (phase 2): `SiteFoundationFrame` reads the Site record (`useSiteRecord`) and, for `site_type=COLDCHAIN`, renders `sites/ColdFoundationViews.tsx` (`ColdFoundationFrame`) from `sites/coldFoundationClient.ts` on the existing `/foundation`, `/foundation/readiness`, `/foundation/sld` routes; MINIGRID is unchanged. A refused Foundation read waits for the record before choosing views.
- Panels: cold-foundation 2 (equal pair), cold-readiness 4 (gateway panel nests 3 and 4), cold-sld 2; refusals are `div.page-refusal` + `ColdSkeletons` with in-panel gaps. Labels `Configured`/`Needs a source`; optional roles shown as `(optional)`.
- Title map: `cold-readiness:2` (gateway from `/gateway-health` `gateway_external_id`, else "No gateway selected") and `cold-sld:1` (Site name; no topology type is declared) in `test/v69PanelTitles.ts`.
- The cold drawing `ColdTopologyDiagram` lives in `sites/SiteSingleLineDiagram.tsx` (shell-overflow guard: SVG only in diagram modules); layered by longest path, scrolls in its own region below 760 px.
- Tests: `sites/__tests__/coldFoundation.test.tsx` (structure in stocked/missing-probe/no-version/unavailable, gaps, vocabulary, exact IDs closed, selection); loading sentence "Loading the site's cold configuration." added to `test/settled.ts`.
- Captures: `.agent/W2-01-evidence/` (9 pairs x 2 widths, 108/108 claims).
- Open: no per-source contact read (panel 3 gap), no capability read (panel 4 "Confidence is not assessed"), no part-function description (SLD panel 2), no topology type; contact is current, not as of `at`; cold binding rows carry no v4 metadata and the acquisition snapshot/`configuration_gaps` path still treats COLDCHAIN as unsupported (W2-02); the generic Foundation read still lists `SITE_TYPE_UNSUPPORTED` for cold Sites (not shown on cold views).

## W2-03 - cold assessment, episodes, Findings and the four cold screens (built, in_review)

Branch `task/W2-03-cold-assessment` (base main `e74309db`; spec `specs/W2-03/spec.md` incl. `D-2026-10-18-w2-03-answers` and the commit-4 freshness amendment). Packet `archive/agent-history/W2-03-review-packet.md`; handoff `archive/agent-history/W2-03-phase-1-handoff.md`.

- Migration `0022_w2_cold_assessment`: `cold_episode`, `cold_episode_revision`, `cold_episode_evidence`, Finding `domain` (`mini_grid|cold_chain`); the fuel consequence trigger fires only for `domain='mini_grid'`.
- Pure rules `analytics/cold.py` (`cold-excursion/1`, `cold-start-response/1`, pinned vectors) and `analytics/cold_reads.py` (one `probe_fresh`, `currentness_state`, cursor codec).
- `ColdAssessmentWorker` (`analytics/assessment_worker.py`) projects assessment, episodes and cold Findings in one transaction; cold store paths in `postgres_assessment_store.py` (sole writer of assessment/episode tables, also hosts the read-only `ColdReadService`) and `postgres_finding_store.py` (`cold_apply`). Intake enqueues `cold_chain` for new accepted v4 cold-role rows (10-min bridge).
- Reads `cold_assessment_api.py`: `/api/sites/{code}/cold/{temperature,backup-chain,findings,findings/{id}}`; default window = latest selected cold window; `disclosure` seam (default allow).
- Frontend: `sites/coldAssessmentClient.ts`, `sites/ColdAssessmentViews.tsx` (`ColdPerformanceFrame`, `ColdFindingFrame`), `sites/coldAssessmentWords.ts`, `sites/coldFormat.ts`; chart `ColdTemperatureChart` in `sites/assessmentGraphics.tsx` (overflow guard). COLDCHAIN switches in `shell/SiteAnalyticsFrames.tsx` (`SitePerformanceFrame` temperature/backup, `SiteFindingFrame` by kind), `coldAssessment` prop on `App`.
- Tests: `backend/tests/test_w203_cold_{rules,migration_postgres,replay_postgres,reads_postgres}.py`, `frontend/src/sites/__tests__/coldRoutes.test.tsx`; captures `.agent/W2-03-evidence/`.
- Open: Cooling subtab and cold Finding Recommendation tab withheld (unbuilt-entry ruling); `Claim boundary` title and mock columns `Power to load`/`Load response` and "Registered simulation" sit on the W1 vocabulary list (filtered in the test, ruling requested); no production source-disclosure policy; no manual-recovery/operational-log source; Analysis link targets the existing evidence Analysis view.

## W2-04 - cold Site, evidence and unpriced consequence (built, in_review)

Branch `task/W2-04-cold-site-evidence-money` (merge-base main `54b0bece`; spec `specs/W2-04/` incl. Run-5/7/8 rulings). Packet `archive/agent-history/W2-04-review-packet.md`; handoff `archive/agent-history/W2-04-phase-handoff.md`.

- Migration `0023_w2_cold_consequence`: append-only `cold_consequence_revision`, `_evidence`, `_work`, `_work_attempt`; trigger-only work on cold FindingRevision/episode revision and source-gate link; adds `batch_publication_link_scope_unique`; guarded downgrade.
- Money: `financials/cold_consequence.py` (pure rules: `PRODUCT_EXPOSURE` degC_min bounds, open episode null high + `OPEN_EPISODE_UPPER_UNKNOWN`, no price/currency), `financials/cold_recompute.py` worker (advisory lock, SUCCEEDED/FAILED attempts); sole writer `adapters/postgres_consequence_store.py`.
- Reads `cold_site_api.py` + `analytics/cold_site_reads.py`: `/api/sites/{code}/cold/{overview,evidence,evidence/analysis,financials,financial-assumptions}`; `accepted_records.total_count` via `PostgresAssessmentStore.accepted_count_on`.
- Frontend: `sites/coldSiteViews.tsx` (five routes, `SelectedWindowBar`, `SOURCE_ROWS`, `RECORD_LABEL`), `sites/coldSiteClient.ts`, `sites/w2-cold-site.css` (route-scoped 1440 widths), `shell/coldSiteRoutes.tsx`.
- Tests: `backend/tests/test_w204_cold_{migration,consequence,worker,reads}.py`, `frontend/src/sites/__tests__/coldSiteViews.test.tsx`; captures `.agent/W2-04-evidence/`.
- Open: Data sources chips overflow at the ruled widths (D1); Accepted records 423/345 px, Record cell wraps 3 lines (D2); unbound-row closed What copy (R1); Q-R9 record links unproven; `SOURCE_GATE_CHANGED` path untested; host suite and a final full backend run outstanding; W2-03 `How each limit is set` 225/120 follow-up.

## post-W6 W2-EV - EV Site screens D3 fixes (built, in_review)

- Rulings `archive/agent-history/post-W6-W2-EV-rulings.md` (cross-card ownership 1-8, Q1-Q31) and `archive/agent-history/post-W6-W1-rulings.md` cross-card contract; packet `archive/agent-history/post-W6-W2-EV-packet.md`; build history `archive/agent-history/post-W6-W2-EV-phase-1-handoff.md`.
- Tabs: `shell/operatorSiteTabs.tsx` optional `hrefs`/`search` override and `operatorSiteTabHref()` (R347 common mechanism; W2-cold and W5-EV-Work consume it); `evSiteRoutes.tsx` `EV_SITE_TAB_HREFS`; `sites/evSelectedWindow.ts` `selectedWindowSearch(read)`, `EvTabs` = ReactNode | (search) => ReactNode. Tabs carry the loaded read's `from`/`to`/`known_at`, never the raw URL; refused/no-window reads carry none; depth pages pass "" (W5-EV-Work).
- Bare `/sites/:id` redirects an `EV_CHARGING` Site to `/ev` (`SiteDetailFrame.tsx`), keeping the query.
- Readiness Financials/Assumptions links (`/ev/financials`, `/ev/financial-assumptions`); unique ExactReferences labels.
- Sessions: lineage link to EV Analysis at the read window; outside-outcomes line (D4 R420); Outcome column CSS; `plural()` exported from `EvAssessmentViews.tsx`.
- Finding: strip joins claim, Site, window; Bounded conclusion "Inspect claim evidence" link at the Finding's window; `FINDING_SECTION_UNAVAILABLE` common copy (cold and EV).
- Refusals (cross-card ruling 5): `RefusedHead`/`RefusedGap`/`NOT_ASSESSED` live in `EvAssessmentViews.tsx`, shared by EV Overview, Evidence, Analysis, Financials, Assumptions, Sessions, Finding and the EV Findings index: strip title "Window cannot be read" for 422, tile labels with `Not assessed`, exactly one in-panel sentence plus technical disclosure, no banner.
- EV Site views: chronology renders all accepted events (no padding); Overview cards plain labels + "View detail →"; Evidence strip "Portfolio evidence", "Review energy →", no padded rows; Analysis times in the Site zone via `sites/siteTime.ts` (exact UTC in `title`); Financials "Energy ↗" only when estimated; billing chips (D4 R421).
- `sites/siteTime.ts` canonical EAT zones incl. Asmara/Djibouti/Mogadishu; `LedgerSiteEvidence.EXTRA_EAT_ZONES` removed (W1-a closeout ruling 5).
- EV Findings index (`sites/EvFindingIndex.tsx`, `SiteFindingsFrame` EV branch, `App.tsx` `evAssessment`): 7 columns, `finding-index-row` column treatment, strip `Scoped to {site} · {n} open · window · global-list note`.
- Captures `.agent/post-W6-W2-EV-recapture/r2/` (122 app captures at dab4d15e; probes in `r2/probe/`).
- Open: cap reading for EV Findings / Accepted records (variable-cell reading passes; Accepted records Source+Value 1344 at 1440 vs 700 if Value is counted) for the Architect; EV depth refused pages raw codes (B16-01) belong to W5-EV-Work; register R420/R421 statuses update after review.

## post-W6 W2-cold - cold Site screens D3 fixes (built, in_review)

- Rulings `archive/agent-history/post-W6-W2-cold-rulings.md` (cross-card ownership 1-8, Q0-Q15); packet `archive/agent-history/post-W6-W2-cold-packet.md`; recapture `.agent/post-W6-W2-cold-recapture/`.
- Refusals (cross-card ruling 5): `refusalText` classifies `COLD_TIME_INVALID`/`COLD_WINDOW_INVALID`/`COLD_WINDOW_TOO_LONG` before the generic 422; refused Temperature/Backup use `PerformanceRefusal` (strip, `Not assessed` tiles, no banner); every cold page carries the sentence once in panel 1 and later panels say `Not assessed` (`RefusedGap repeat` in `coldSiteViews.tsx`, `REPEATED_GAP` in `ColdAssessmentViews.tsx`). Window refusals show no requested-window line.
- Cold Findings index: `ColdFindingIndex` (`ColdAssessmentViews.tsx`), COLDCHAIN branch first in `SiteFindingsFrame` (then EV, then mini), `App.tsx` `coldAssessment`; shared `LensChips`; `finding-index-row` treatment; D1 R435/R436 visible labels.
- Overview: five "View detail →" cards (Maintenance D1 R437 label in the card), strip outcomes joined from `getBackupChain` by `evidence_id`, SLD link, deduplicated limitations. `ColdSiteRoutes` gains `sld`, `workMaintenance`, `portfolioEvidence`.
- Evidence "Portfolio evidence" / "Review cooling →"; Analysis Measured/Sent/Received in the Site zone via canonical `sites/siteTime.ts` (missing zone: `UTC; Site time zone unavailable`).
- Tabs: `coldTabSearch(site, params)` feeds the W2-EV `OperatorSiteTabs` search override on cold Overview, Evidence, Performance, Findings, Finding, Financials, Health.
- Open: Work/Scenarios tab window and depth copies (W5-cold-Work); register statuses R241-R261, R435-R437 after review; Not-determined 390 wrap not producible.

## post-W6 W5-EV-Work - EV depth and Work D3 fixes (built, in_review)

- Branch `task/post-W6-W5-EV-work` (main `104e9c33`); rulings `archive/agent-history/post-W6-W5-rulings.md` 3-5; packet `archive/agent-history/post-W6-W5-EV-packet.md`; evidence `.agent/post-W6-W5-EV/`.
- `EvAvailability.tsx` `EvDepthRefusal` is the one refusal block for all four depth pages (RefusedHead + RefusedGap + `Read without a selected window` link for window refusals + Reload for 503/409/unreached); old `data-ev-depth-error` marker is gone. `connectorHoursText` uses `plural`, tiles show decimal `connector-h` with exact `X h Y min` in the title.
- `EvEnergy.tsx` `bridgeRows`: WITHHELD + null quantity shows metered kWh in row 1; visible `MOCK DEVIATION D1 (R06)` line. `ev_site_reads.py` `MONEY_COPY["STALE_BASIS"]` = `No stored gross tariff estimate matches the current evidence.` (wire unchanged).
- `sites/evSelectedWindow.ts` `ReportSelected` / `useReportSelectedWindow`: depth pages report the window they read; `SiteHealthFrames.tsx` EV uses `EvHealthWithTabs`; `shell/evSiteRoutes.tsx` `evWorkTabHrefs/evWorkTabSearch` feed the Work mounts (explicit valid URL window only).
- SAF `DomainActionShell`: EV `actionWindowRefusal` (evWorkPresentation.ts) refuses before any read; presentation fields `reloadLabel`, `technicalDetail`, `headings`. `DomainActionUnknownSection`: for COLDCHAIN and EV_CHARGING, `/plan /execution /history /evidence` render `This address is not served` with `Open this Action's verification`, no read, no redirect (also for a W1 ID: residual risk in the packet). Bare route still redirects (R222 `/overview` alias unchanged).
- `tools/w504_ev_work_walkthrough.py` Site Work router passes `details=` (R373 EV case-detail 503 fix). `evHealthDepth.css`: Asset column 40/30/30 at <=640 px (R470).
- Cap tooling: `.agent/post-W6-W5-EV/tools/measure-caps.mjs` (closed height, labelled 160-char DOM stress probe, refusal block, text probe), `run_ev_all.sh`, `startvite.ps1` (start Vite with Start-Process; a bare `nohup` Vite died twice). Provisional caps for unruled EV panels are in the packet; ruled ev-health 400/800 and ev-work 550/800 hold.
- Open: unknown/pending/stale EV modes, missing-meter, historical depth, authored scenario, non-Open Action states have no unmodified producer (selected-DTO tests only); backend full suite held by the coordinator. Register: R345-R350 closed, R06 noted, R470 added.
- Fix round (R350 ruling 1, `archive/agent-history/post-W6-W5-EV-r350-rulings.md`): `/plan /execution /evidence /history` on cold/EV go through `DomainActionRoute` with `unserved`: domain probe first; loaded domain Action = `DomainActionUnknownSection` at the same URL (no redirect, no W1 read); non-loaded probe = `w1()` with the original section. `evActionRefusal` checks `INVALID_KNOWN_AT` before unreached; `evWorkTabSearch` carries a valid UTC `known_at` alone. Evidence `.agent/post-W6-W5-EV-fix/` (`cap.sh`, targets). Producers have no W1 Action: the W1-ID landing is a W1-shaped unknown ID; a loaded W1 section is jsdom-only.

## post-W6 W5-cold-Work - cold depth and Work D3 fixes (built, in_review)

- Branch `task/post-W6-W5-cold-work`; rulings `archive/agent-history/post-W6-W5-rulings.md` 1-2; packet `archive/agent-history/post-W6-W5-cold-packet.md`; handoff `archive/agent-history/post-W6-W5-cold-handoff.md`.
- `defaultWorkWindow` (`sites/workClient.ts`) is `[today−6d, tomorrow)` UTC for every Site Work consumer (cold/EV Actions, all cases incl. mini).
- `DomainWorkWindow` requires `basis` (`actions|incidents|maintenance`) and states `DOMAIN_WORK_WINDOW_BASIS` under the control; mini cases form has none.
- `DomainActionPresentation.refusal?` maps a refusal to `{message, retry}`; cold uses `coldActionRefusal` (exact code, Retry only 503/unreached, `role="alert"`); EV absent = unchanged.
- `relatedSentence` states linked VERIFICATION_WINDOW (with record) and linked CANCELLED; cold `coldDepthStateNotice` / `scenariosStateNotice` make UNKNOWN and pending notices row/count-aware; R25 subtitle replaced.
- Cooling badges carry W4 `status-tone--*` classes (CSS `ui/primitives.css:1202`, verified). R339: the Work Actions and cases tab rows take `coldTabSearch(site, params)` (cold only; mini/EV bare); Scenarios/Health/Cooling came with W2-cold.
- Evidence `.agent/post-W6-W5-cold-recapture/` (cold b14/b15 sets, EV, mini, tab row; all pass except the baseline 6+6 state-panel pairs and forbidden/unavailable cold-action 2 each). Open: R344 VERIFICATION_WINDOW/linked CANCELLED no producer; ruled-cap stress clones not re-measured; W5-EV edits the same shared files next. Rows R334/R336-R339/R344 closed, R460/R461 added.
## FIX-COLD-DRAIN - the scheduled tick drives the cold and EV producers (built, in_review)

Branch `task/FIX-COLD-DRAIN-tick` (from main `ce5df006c`). Spec: plan2 `specs/FIX-COLD-DRAIN/spec.md` U1-U4. Packet
`archive/agent-history/FIX-COLD-DRAIN-packet.md`. No migration, no reader change.
- Tick order per Site (`scheduling/tick.py` `_site`): `S3: s3 -> cold_assess -> ev_assess` · `MINI` · `OPPORTUNITY` · `S4` ·
  `CONSEQUENCE: consequence -> cold_consequence -> ev_consequence`. Each new child re-checks the Site claim with the existing
  marker (`set_stage("S3")` / `set_stage("CONSEQUENCE")`; the 0030 CHECK is unchanged) and is its own killable child.
- Failure names `COLD_ASSESS`, `EV_ASSESS`, `COLD_CONSEQUENCE`, `EV_CONSEQUENCE`; the first failure is kept and later children
  run. A failed consequence *item* keeps the drain `OK` (`failed` count) and retries under the worker's `retry_due_at`; no Site
  back-off (Architect Q1 ruling (b)).
- Head counts are summed into the existing columns: `record_s3(s3 + cold + ev)` once after the S3 group and
  `record_consequence(mini + cold + ev selected/deferred)` once after the drains. A non-OK child adds 0; a group whose every
  child failed writes nothing (the earlier head counts stand, as before for a failed `s3`).
- `TickLimits`: `domain_jobs_per_site=10`, `domain_assess_seconds=120` (< `DOMAIN_JOB_LEASE_SECONDS` 300),
  `domain_consequence_seconds=60`; `site_lease_seconds` default 600 -> 960.
- Stages (`scheduling/stages.py`): `cold_assess`/`ev_assess` lease at DB time through `build_cold/ev_assessment_worker(url,
  clock=db_clock(url), lease=...)` (`analytics/composition.py` now passes `**kw` through, defaults unchanged); `deferred` from
  `live_jobs(cold.EXCURSION_ANALYTIC|ev.SESSION_ANALYTIC, domain)`. `cold_consequence`/`ev_consequence` run the unedited W2-04/W2-07
  workers' `run(t, s, limit, now)` and compute the `consequence` shape locally.
- Tests: `test_fix_cold_drain_stage.py` (T1-T5, fake runner), `test_fix_cold_drain_tick_postgres.py` (P1-P4, in-process real
  stages). Tick-order and lease literals updated in `test_w402_mini_stage.py`, `test_w403_opportunity_stage.py`,
  `test_w402_mini_stage_postgres.py`.
- Left open: R624 (an excluded-lifecycle Site with only cold/EV work is not discovered; no cold/EV counts in `health.py`), and
  four more child processes per visited Site in a deployment (fewer Sites per 240 s tick).
