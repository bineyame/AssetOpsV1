# CH-5b1 pre-flight (guards and tools)

Builder: Claude (Opus), 2026-11-05. Branch `task/CH-5b1-guards-tools` from main `8777bc0f8`. Paths: `B/` =
`backend/assetops_backend/`, `F/` = `frontend/src/`. Scope: build sheet CH-5b "Build units" CH-5b1 entry (R5, R6, R7,
P2, P4).

## Facts from code

- **App factory (P2).** `B/main.py:210` `create_app(...)`; the chain router is wired at `B/main.py:637-641`
  (`build_chain_router(..., policy_versions=chain_policy_versions)`), `app = create_app()` at `B/main.py:704`.
  No config path is injectable into `create_app`; the chain configs load from repo files through lru-cached
  defaults (`B/chain/adapters/file_chain_config.py:62-95`). No test overrides `DEFAULT_REGISTER_PATH` /
  `DEFAULT_LIFECYCLE_PATH` or clears those caches (grep over `backend/tests`, `tools`: 0 hits). 37 test files call
  `create_app(` (102 calls); all run with the repo config present.
- **Layering.** `tools/checks/configuration-persistence.ps1:187-196`: the `chain` package's adapters are imported
  only by `B/chain/composition.py` (today: `composition.py:11,113,192`, plus `postgres_thread_sources.py`, an
  adapter). So `B/chain/graph.py` stays pure and the file loading goes in `composition.py`.
- **R6 inputs.**
  - Register: `config/chain/event-register-v1.yaml` (11 events, 7 `inputs`), parsed by `B/chain/events.py:75`
    `parse_register` (schema only; `tools/checks/test_event_register.py:71` `problems()` already checks roles,
    analytics, job domains against producers).
  - Measures: `B/chain/measures.py:43-69` `MEASURES` (7). Adapter keys: `B/chain/measure_impls.py:459-462`
    `build_measure_set` (7 classes, class-level `key`).
  - Lifecycle: `config/chain/thread-lifecycle-v1.json` `clean_day_measures` (5 mechanisms), parsed at
    `B/chain/lifecycle.py:97-103`.
  - Map: `B/outcomes/outcome_map.py:16-35` `ENTRIES` (15 keys: 4 `FINDING:`, 3 `SIGNAL:`, 8 `WARNING:`),
    `DOMAIN_ALIAS` `:36-38`, `thread_signal_key` `:110-114`, `_THREAD_SIGNAL_MECHANISMS = ("PRODUCTIVE_USE_HEADROOM",)`.
  - On main all 7 measures have an `inputs` entry and every lifecycle measure exists in `MEASURES`.
- **R5.** `tools/chain_perf_probe.py` (CH-5a1/CH-5c): `URLS` `:35-43` (3 boards, summary, portfolio, findings; no
  `/chain` route), `BUDGETS` `:47` (board 1000/300/60 000; portfolio 1000/300/100 000), `one()` `:78`, `client()`
  `:54` (needs `--work` with `keys.json`), cold = one child process per run `:173-182`, `--store on|off` `:162`.
  Chain routes: `B/chain_api.py:102` (Site chain), `:135` (thread), `:168` (estate chain).
  Design §11b budgets (`implementation-logic-design-proposal.html:2417-2424`): board and Portfolio <= 1 s cold,
  <= 300 ms p95 warm; payload <= ~100 KB Portfolio, <= ~60 KB board; "Why?" <= 50 ms; tick chain stage <= 50% of
  its stage limit; snapshot rebuild <= 50 ms per measure-day.
- **DB target.** The CH-5c polish clone (`assetops_chainclone_ch5c_test`) was dropped (`review-packet-CH-5c.md:208`).
  `tools/chain_clone.py:3-5,32` creates `assetops_chainclone_<name>_test` from `assetops_polish_full_test`
  (template; refuses while polish has sessions). The only polish `keys.json` is under polC (forbidden). The keys are
  two random cursor keys (`tools/demo_combined.py:64,397`).
- **No `dot` binary** and no `graphviz`/`pydot` module in the plan2 venv; `yaml` is available.
- **check-all.** `tools/check-all.ps1:56-69`, 14 guards; the three new lines go after `:69`.

## P4: hard-wiring counts today (frontend/src, non-test files; basis below)

Counting basis (the §13 list): `cmp` = `site_type|siteType` `===`/`!==` against a string literal or a `*SITE_TYPE`
constant (not `typeof`, not `=== undefined`); `lit` = the quoted Site-type values `MINIGRID|COLDCHAIN|EV_CHARGING`;
`code` = `KOBO|COLD-LAB|EV-LAB-\d{3}`; `oid` = `MG|CC|EV-\d`; `api` = a quoted `/api` string in a `.tsx` component;
`href` = `href=`/`to=` bound directly to a server field (`x.href`, `x.url`, `x.link`, `x.links.y`). Excluded:
`__tests__`, `*.test.*`, `/test/`, `F/blocks/vocabulary*`, `F/views/registry.ts` (neither exists yet).

| File | cmp | lit | code | oid | api | href |
|---|---|---|---|---|---|---|
| App.tsx | 0 | 0 | 0 | 0 | 2 | 0 |
| estate/estateClient.ts | 0 | 3 | 0 | 0 | 0 | 0 |
| estate/EstateEvidence.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| estate/EstateFinancials.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| estate/EstatePortfolio.tsx | 0 | 1 | 0 | 0 | 1 | 2 |
| estate/findingIndex.tsx | 0 | 0 | 0 | 0 | 0 | 4 |
| estate/portfolioWords.ts | 0 | 3 | 0 | 0 | 0 | 0 |
| shell/coldScenarioChoiceClient.ts | 0 | 0 | 1 | 0 | 0 | 0 |
| shell/coldSiteRoutes.tsx | 1 | 1 | 0 | 0 | 0 | 0 |
| shell/EvRunSetupFrame.tsx | 1 | 2 | 0 | 0 | 0 | 0 |
| shell/evScenarioChoiceClient.ts | 0 | 0 | 1 | 0 | 0 | 0 |
| shell/evSiteRoutes.tsx | 3 | 3 | 0 | 0 | 0 | 0 |
| shell/RunCommitPanel.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| shell/simulatorLabRoutes.tsx | 0 | 0 | 0 | 0 | 8 | 0 |
| shell/SiteAnalyticsFrames.tsx | 27 | 31 | 0 | 0 | 0 | 0 |
| shell/SiteDetailFrame.tsx | 3 | 3 | 0 | 0 | 0 | 0 |
| shell/SiteEvidenceFrame.tsx | 1 | 1 | 0 | 0 | 0 | 0 |
| shell/SiteFoundationFrame.tsx | 0 | 4 | 0 | 0 | 0 | 0 |
| shell/SiteHealthFrames.tsx | 3 | 3 | 0 | 0 | 0 | 0 |
| shell/siteTemplateCatalogClient.ts | 1 | 0 | 0 | 0 | 0 | 0 |
| sites/assessmentAnalysis.tsx | 0 | 0 | 0 | 0 | 0 | 2 |
| sites/CapabilityReadiness.tsx | 0 | 0 | 0 | 0 | 1 | 0 |
| sites/ColdAssessmentViews.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| sites/ConsequenceHistory.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| sites/domainActionClient.ts | 0 | 2 | 0 | 0 | 0 | 0 |
| sites/MiniPerformance.tsx | 0 | 0 | 0 | 0 | 0 | 3 |
| sites/periodStrip.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| sites/siteDirectoryClient.ts | 1 | 0 | 0 | 0 | 0 | 0 |
| sites/SiteFindingEvidence.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| sites/SiteFoundationChange.tsx | 2 | 2 | 0 | 0 | 0 | 0 |
| sites/SiteWorkActions.tsx | 0 | 0 | 1 | 0 | 0 | 0 |
| sites/siteWorkCases.tsx | 1 | 3 | 0 | 0 | 0 | 2 |
| sites/sldViewModel.ts | 1 | 1 | 0 | 0 | 0 | 0 |
| work/GlobalIncidents.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| work/globalWorkClient.ts | 0 | 7 | 0 | 0 | 0 | 0 |
| work/globalWorkParts.tsx | 0 | 0 | 0 | 0 | 0 | 1 |
| work/workRequestShared.tsx | 0 | 0 | 0 | 0 | 0 | 2 |
| **Total** (files) | **46** (13) | **70** (16) | **3** (3) | **0** | **12** (4) | **24** (15) |

(`cmp` 46 vs the design's 45: the design counted `===` only; this adds `!==`. The guard's final regex removes the
one `typeof … === "string"` hit in `runSetupClient.ts` if it survives.) **R8 drops** (CH-5b3, not this unit):
`shell/SiteAnalyticsFrames.tsx:468-598` holds 5 `cmp` and 5 `lit`; `sites/SiteFindingIndex.tsx` has 0 today. The
baseline file is generated by the guard itself, so the committed numbers are the tool's, not this table's; any
difference is listed in the packet.

## Lane-1 overlap (CH-5c2)

None on `chain/response_store.py`, `chain/watermark.py` or migration 0050. Shared files, small additive hunks:
`B/chain/composition.py` (one new loader function), `B/main.py` (one call beside `:641`), `tools/check-all.ps1`
(three lines after `:69`). `tools/chain_perf_probe.py` is imported, not edited.

## Questions (each with the default I build if no ruling comes)

1. **R6 "every `ENTRIES` source maps to a measure or a mechanism".** 10 of 15 keys fail that on main: the 8
   `WARNING:*` and `SIGNAL:EVIDENCE_GAP` / `SIGNAL:EVIDENCE_READINESS` have no measure and no lifecycle mechanism.
   *Default:* the rule binds the `FINDING:` keys and the `SIGNAL:` keys of thread mechanisms
   (`_THREAD_SIGNAL_MECHANISMS`): each must name a `clean_day_measures` mechanism. The other keys are checked only
   for "every reference resolves" (each outcome key or alias resolves for some domain) and are listed by the `check`
   output as "not chain-sourced (CH-8)". "No orphan" = every lifecycle mechanism reaches an `ENTRIES` key through
   `thread_signal_key`, and every register `inputs` key is a `MEASURES` key. "Every reference resolves" also covers
   each `MeasureSpec.adapter` being a `build_measure_set` key.
2. **Layering.** *Default:* `B/chain/graph.py` is pure (`check(register, measures, lifecycle, entries, adapters)`,
   `dot(...)`); `B/chain/composition.py` gets `check_declared_chain_graph()` that loads through the adapter;
   `main.py` calls it beside `:641`; `python -m assetops_backend.chain.graph check|dot` imports composition lazily.
3. **SVG without Graphviz.** *Default:* `graph dot` writes the DOT text to `Docs/demo-sprint/chain-graph.dot` and a
   pure-Python column-layout SVG (events → measures → mechanisms → map keys → outcomes) to
   `Docs/demo-sprint/chain-graph.svg`; both committed, regenerated deterministically (a test asserts the committed
   files equal a fresh render).
4. **Budget routes and families (R5).** *Default:* `perf_budget.py` imports the probe's helpers (no probe edit) and
   measures the probe's six URLs plus `/api/sites/{KOBO-001,COLD-LAB-001,EV-LAB-001}/chain` and `/api/estate/chain`
   on the probe's windows. Families: boards and Site chain → board budget; Portfolio and estate chain → portfolio
   budget; summary and findings → reported, no budget (as the probe). `why_trace_ms`, `tick_chain_stage_fraction`
   and `snapshot_rebuild_ms_per_measure_day` are in `perf-budgets-v1.json` but marked `"measured_by": null` and
   printed "not measured (CH-5b2 / E4)". p95 is nearest-rank over the warm runs. A test asserts the probe's
   `BUDGETS` equal the JSON.
5. **Fail vs report.** *Default:* `--database-url` exits 1 on a breach; `--report` prints the same table and exits 0
   (the per-slice mode, EX-3). `--fixture` self-tests: `pass.json` must pass and each `breach-*.json` (cold, warm
   p95, bytes, missing route) must fail with its named reason.
6. **The one DB run.** *Default:* `chain_clone.py create ch5b1 --migrate`, `chain.backfill`, `chain_clone.py settle
   ch5b1`, then `perf_budget.py --database-url <clone> --work <worktree>/var/ch5b1_perf --report` once, store on
   (default) and no pre-build, 3 runs (cold children cost ~2 s each × 10 URLs), with a fresh `keys.json` of two
   `secrets.token_hex(32)` keys written to that work dir (nothing read from polC). Then `chain_clone.py drop ch5b1`.
7. **Ratchet scope (R7).** *Default:* counts per file per pattern (basis above); a file absent from the baseline
   counts from 0 everywhere, not only under `F/blocks/` (a new file with a Site-type literal fails); a rename counts
   as a new file. `--shrink` rewrites the baseline with `min(old, new)` per cell and drops zero rows; it never adds a
   file or raises a cell. The guard prints the files that shrank, so a reviewer sees when `--shrink` is due.
