# Build sheet CH-5b: "Why?" trace, ETag, performance guard, shared blocks and the one finding list

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). The rulings in §1 are logged in the plan as **CH5b-R**.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-5b row (5 units → **6**, R10), lane 1 after CH-5a2. It depends on MA-1, which is approved.
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - §5b.5 ("Why?" trace, catalogue graph checks; AG-19);
  - §11b (budgets, ETag, `perf_budget.py`);
  - §8b (building blocks, vocabulary layer, plug-in views; AG-28 to AG-32);
  - §13 (frontend hard-wiring guard, fourth-type contract test).
- Register: I-13. The budgets are EX-3.
- Mock: MA-1 in v70:
  - **M2** "Why?" popover: `frontend/mockups/v70/outcomes.js:122-144` (`WHY`, `whyBtn`, `whyPop`, `openWhy`), placed on rows at `:161` and on Portfolio cards at `:193-194`;
  - **M1** day line (`ob-days`);
  - **M4** problem-history timeline.
  - Measurements: `.agent/MA-1-mock-measurements.md`.
- Branch: `task/CH-5b-why-etag-blocks`, cut from main after CH-5a2 merges. It needs MD-0 L2m/L3m (`.agent/build-sheet-MD-0.md`).
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`. Lines are to `e207f328f`. The CH-5a2 names (`B/chain_api.py`, `B/chain/refs.py`, `B/chain/read.py`, `routeFor`) are as specified in `.agent/build-sheet-CH-5a.md` Part B. Pre-flight P1 re-anchors them to the merged code.

## 0. Result and boundary

**Observable result.**
- **"Why?"** A button sits beside each outcome value on the Site board (each of the four rows) and on each of the four Portfolio cards. It opens a dialog, which is a bottom sheet at 390 px. The dialog shows:
  - the value in one sentence;
  - "Comes from" (2–4 lines);
  - "Days used" (the M1 day line);
  - "What would change it";
  - a link to the evidence screen.
- The text comes from a server-built trace over stored ids. The trace is ≤ 50 ms on L2m, and the same trace is in the JSON for audit.
- **ETag.** The three chain endpoints and the two "Why?" endpoints return an `ETag`. An unchanged page answers `304` to `If-None-Match`.
- **Budget guard.** `tools/checks/perf_budget.py` runs in fixture mode in check-all and in DB mode in the finish checks and E4.
- **Shared blocks** (`F/blocks/`), used by the board and Portfolio:
  - `OutcomeRow`;
  - `MeasureTile` (with the M1 day line);
  - `FindingCard`;
  - `ActionTimeline` (M4);
  - `EvidenceTrace` (M2).
- **One finding list.** The Site Findings page renders **one** `ThreadList` over `/api/sites/{code}/chain` threads for every Site type. The Site-scoped lenses (All, Cost, Risks, Opportunities) are real routes. This closes MOCK DEVIATION D5 at `F/sites/SiteFindingIndex.tsx:133`.
- **Graph check.** `python -m assetops_backend.chain.graph check` validates the declared chain config at startup and in check-all.
- **Hard-wiring guard.** `tools/checks/frontend-hardwiring.mjs` joins check-all as a **ratchet**: today's counts are the baseline and may only shrink.

**Not in this slice.**
- Outcome nodes: the earnings, KPI and potential slots and the Grow three parts (M3); OutcomeEvaluator; Portfolio from EstateChain (all CH-6). `OutcomeRow` has the three slots; CH-6 fills them. Until then the slots show the CH-5a2 row headline.
- Detail pages (CH-10a/b), the per-type plug-in chart views beyond registering the existing ones, and the full catalogue (CH-8).
- Any change to a value, state, rule or copy literal, except the new copy in §2.3. A changed value is High.

## 1. Architect rulings (CH5b-R; none needs the owner)

| # | Gap | Ruling |
|---|---|---|
| R1 | The design trace (§5b.5) is a node tree. MA-1 shows plain lines. | **One trace, two views.** `B/chain/why.py` `trace(reader, site, category, window, k) -> Trace`: `nodes` (each `{kind, label_key, ids, basis, grade}`), plus `text` = `{say, comes_from[2..4], days_used, would_change, evidence_ref}`, rendered once by `B/chain/vocabulary.py` (PC-1 claims for counts). The browser shows only `text`. `nodes` is for audit and tests. A node with no stored id is not emitted ("nothing extra is stored"). |
| R2 | Which outcome the trace walks. | `outcome_map` only (OL-1): the moved and checked sources of the category, from `categories_for` / `thread_signal_key`. No outcome id or map key is built in `why.py`. Node kinds: `row_state`, `measure_day` (snapshot rows of the window), `analytic` (selected run ids), `finding` (head revision + cited count), `thread` (state + since), `action` (+ verification outcome). |
| R3 | `would_change`. | It comes from the trace, never invented: the first missing input in this order: a PARTIAL/NO_DATA/PENDING day of a used measure → "Checking {n} more days"; an open thread with no Action → "An agreed action"; an Action without a verdict → "The check after the change". Otherwise "New readings that differ". Each line is a vocabulary template (§2.3). |
| R4 | The ETag key (§11b) must change whenever the body can change. Bodies depend on facts (outbox), on derived rows (snapshots and thread events, written after the drain), and on settledness (CH5a-R R8). | `etag = sha256(schema_version, sorted site ids, window, known_at or "live", policy_versions, CODE_VERSION, max(event_outbox.recorded_at, event_id) ≤ k, max(site_day_snapshot.recorded_at) in window, max(finding_thread_event.seq) for the Sites, the R8 settled flags)`. One SQL statement per request, memoised in the read scope. `CODE_VERSION` is the app's build id, so a deploy invalidates every ETag. **No server-side body memo** in this slice: the 304 skips the composition only when `If-None-Match` matches, which the probe measures. |
| R5 | `perf_budget.py` in check-all must not need a demo DB (plan §4.3). | **Two modes.** `--fixture` reads `tools/checks/fixtures/perf_budget/*.json` (recorded probe outputs) and self-tests the budget logic. `--database-url` runs `chain_perf_probe` (CH-5a1) and **fails** on a breach. The budgets live in `config/chain/perf-budgets-v1.json`, copied from design §11b and never edited to pass. The finish checks run DB mode. A per-slice run is report-only until E4 (EX-3: report, never relax). |
| R6 | Graph check without the CH-8 catalogue. | It validates what is declared today: `config/chain/event-register-v1.yaml` (CH-1b), `B/chain/measures.py` `MEASURES`, `config/chain/thread-lifecycle-v1.json` `clean_day_measures`, and `outcome_map` `ENTRIES`. Checks: every reference resolves; every measure has an event-register input; every lifecycle mechanism's measures exist; every `ENTRIES` source maps to a measure or a mechanism; no orphan entry. It runs in the app start (`B/main.py`, beside the router wiring, P2) and in check-all. `dot` output goes to `Docs/demo-sprint/chain-graph.svg` via `python -m assetops_backend.chain.graph dot` (generated, committed). |
| R7 | Hard-wiring guard (§13) vs today's 45 `site_type ===`/`siteType ===` comparisons in 15 files (counted again on this head). | **A ratchet, not a wall.** It counts the §13 patterns per file outside `F/blocks/vocabulary*` and `F/views/registry.ts`: Site-type literals and comparisons, Site codes, `MG-\d`/`CC-\d`/`EV-\d`, `/api` in components, and a rendered server `href`. It compares the counts with `tools/checks/fixtures/frontend-hardwiring-baseline.json`. Any file's count rising fails the guard. New files under `F/blocks/` must have 0. The baseline is regenerated only downward (`--shrink`). CH-10a turns it into the full guard. |
| R8 | One finding list. Today there are three (`SiteFindingIndex.tsx` 1,061 lines, `EvFindingIndex.tsx`, the cold index), chosen in `F/shell/SiteAnalyticsFrames.tsx:468-598`. | `F/blocks/ThreadList.tsx` renders `chain.threads` with `FindingCard`, filtered by the lens (`threads[].lens`, CH5a-R lens rule). Routes: `/sites/:code/findings` (All), `/sites/:code/findings/cost`, `/sites/:code/findings/risks` and `/sites/:code/findings/opportunities`, built by `routeFor` `SITE {view}`. The three old lists stay **reachable only as detail** (the assessment tables under the existing `findings/:siteId/:assessmentId` patterns, `F/App.tsx:496`). The frame switch at `SiteAnalyticsFrames.tsx:468-598` for the list goes away. This shrinks the R7 baseline. |
| R9 | Blocks vs the mock. | Each block reproduces MA-1/v70 markup classes (`ob`, `ob-sum`, `ob-days`, `why-btn`, `conf-pop why-pop`, `value-card oc-pfcard`). Any departure is a MOCK DEVIATION with a label. `EvidenceTrace` reuses `ExplainerDialog`'s focus handling (`F/sites/OutcomeBoard.tsx:238-316`), moved into `F/blocks/Dialog.tsx`. The board imports it from there, so there is no second focus trap. |
| R10 | Size. | 6 units (plan 5): the one ThreadList (R8) moved here from CH-4 (`build-sheet-CH-4.md` §0). The total grows by 1 (lane 1). Still ≤ 6, so no split. |

## 2. Contract (additive)

### 2.1 `GET /api/sites/{code}/chain/why?category=OPTIMIZE_COST&from&to&known_at`

```json
{"schema_version": "outcome-chain-why-1", "site": {"code": "KOBO-001"}, "category": "OPTIMIZE_COST",
 "window": {"from": "…", "to": "…", "known_at": "…"},
 "text": {"say": "…", "comes_from": ["…", "…"], "days_used": "<the M1 line>", "would_change": "…",
          "evidence_ref": Ref},
 "nodes": [{"kind": "row_state", "label_key": "why.row_state", "ids": [], "basis": null, "grade": null}, "…"]}
```

- Errors as the chain route: `CATEGORY_UNKNOWN` (422) for a category outside the four.
- **Estate:** `GET /api/estate/chain/why?category&from&to` gives the same shape, with `sites: [{code, text, nodes}]` and an estate `text.say`. Money is never summed (design A6).

### 2.2 Headers

- Every chain and why response carries `ETag: "<R4 hex>"` and `Cache-Control: private, no-cache`. A matching `If-None-Match` returns `304` with an empty body.
- The frontend chain client sends `If-None-Match` from a per-URL memory map, and reuses the last body on `304`.

### 2.3 Copy (vocabulary templates, `B/chain/vocabulary.py`; V guard)

| Key | Text |
|---|---|
| `why.title` | `{site} · {category name}` (category names as the board) |
| `why.from.measure` | `{measure label} on {k} checked day{s}` (+ ` × declared price {p} per kWh` when priced) |
| `why.from.finding` | `{finding title}, seen {n} time{s} since {first day}` |
| `why.from.action` | `{action code} · {action state label}` |
| `why.change.days` | `Checking {n} more day{s}` |
| `why.change.action` | `An agreed action` |
| `why.change.verdict` | `The check after the change` |
| `why.change.readings` | `New readings that differ` |
| `why.evidence` | `{site} evidence →` |

Each line is a MOCK DEVIATION candidate against MA-1 M2 copy. The packet lists them old (mock) → new.

## 3. Files

| File | Change |
|---|---|
| `B/chain/why.py` (new) | `trace`, the node builders, `would_change` (R1–R3) |
| `B/chain/etag.py` (new) | the R4 query and hash; `CODE_VERSION` |
| `B/chain/graph.py` (new) | `check`, `dot` (R6) |
| `B/chain_api.py` | the two why routes; ETag/304 on all chain routes (inside `perf.route`) |
| `B/chain/vocabulary.py` | the §2.3 templates |
| `B/main.py` | graph check at start (P2) |
| `config/chain/perf-budgets-v1.json` (new) | the design §11b numbers |
| `tools/checks/perf_budget.py`, `tools/checks/fixtures/perf_budget/` (new) | R5 |
| `tools/checks/frontend-hardwiring.mjs`, `tools/checks/fixtures/frontend-hardwiring-baseline.json` (new) | R7 |
| `tools/check-all.ps1` | three lines: graph check, `perf_budget.py --fixture`, hard-wiring ratchet |
| `F/blocks/{OutcomeRow,MeasureTile,FindingCard,ActionTimeline,EvidenceTrace,ThreadList,Dialog}.tsx` (new), `F/blocks/blocks.css` | §1 R8, R9 |
| `F/sites/OutcomeBoard.tsx` | rows become `OutcomeRow`; the Why button; the dialog from `F/blocks/Dialog.tsx` |
| `F/estate/PortfolioOutcomes.tsx` | cards become `OutcomeRow` (card variant) + Why. Card rules stay as they are until CH-6 |
| `F/shell/SiteAnalyticsFrames.tsx:468-598`, `F/App.tsx` | the ThreadList routes (R8) |
| `F/sites/SiteFindingIndex.tsx:94-137` | lens chips become links; D5 label removed |
| `F/shell/chainClient.ts` (CH-5a2) | `If-None-Match` and the `304` reuse |

## 4. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| Three per-type finding lists (§8b item 3) | Replaced on the Site Findings page | **Fixed** (R8). The old lists remain only as assessment detail, a labelled keep → CH-10a |
| Site-type switch for the list (`SiteAnalyticsFrames.tsx:468-598`) | Removed | **Fixed** |
| Browser card rules (`PortfolioOutcomes.tsx:117-222`) | Wrapped in `OutcomeRow`, not edited | **Labelled keep → CH-6** |
| Disabled lens chips, D5 (`SiteFindingIndex.tsx:133`) | Edited | **Fixed**, and the MOCK DEVIATION label is retired |
| Unit literals in `OutcomeBoard.tsx`/`PortfolioOutcomes.tsx` (§8b item 9) | Moved where a block renders them | **Fixed** for the moved ones; the rest is a ratchet baseline |

**OL-1.** `why.py` reads outcome links only through `outcome_map`. No outcome-id literal goes in `F/blocks/` (the R7 guard enforces 0). The CH-6 ratchet baseline does not grow.

**MOCK DEVIATION candidates.**
- **MD-CH5b-1:** the §2.3 lines vs the mock's example lines.
- **MD-CH5b-2:** OutcomeRow's three slots show the CH-5a2 headline until CH-6.
- **MD-CH5b-3:** the old assessment tables remain under detail routes.

## 5. Test ladder

1. **L0** `tools\run-host-tests.ps1 -- backend/tests/test_ch5b_why.py backend/tests/test_ch5b_etag.py backend/tests/test_ch5b_graph.py`:
   - `trace` over a fixture reader for each category × Site type, including the MD-0 shapes:
     - a COMPLETE week;
     - GAP-K7 (NO_DATA) → `why.change.days`;
     - an open thread with no Action → `why.change.action`;
     - CHANGE_APPLIED → `why.change.verdict`;
   - no node without ids;
   - `text` equals the §2.3 literals;
   - ETag stability (same inputs → same tag) and change (each of the 8 R4 inputs flips it);
   - the graph check passes on main's config and fails on one mutation per R6 rule.
2. **L2m** `backend/tests/test_ch5b_why_postgres.py` on `mechanism_db()`:
   - Kobo D13 OPTIMIZE_COST trace ≤ 50 ms (5-run median, reported), nodes include the D4/D11 Findings and ACT-K1's verification;
   - an ETag `304` round trip;
   - after `late_fill(KOBO-001, D7)` and its consume, the Kobo ETag changes, and the Cold ETag does not.
3. **L1 / frontend:** `npx vitest related --run src/blocks/*.tsx src/sites/OutcomeBoard.tsx src/estate/PortfolioOutcomes.tsx src/shell/SiteAnalyticsFrames.tsx`:
   - blocks from the L1 goldens;
   - Why opens, traps focus and closes, and is a bottom sheet at 390 px;
   - ThreadList for each lens and Site type, plus a **synthetic fourth Site type** from fixture contracts with no code change (§13 fourth-type test);
   - `304` reuse in the client.
4. **Existing, scoped:**
   - `outcomeBoard.test.tsx`, `estatePortfolio.test.tsx`, `s404SiteFindingIndex.test.tsx`;
   - `test_ch5a2_*`, `test_out_b4_route.py`;
   - `tools/checks/test_chain_coherence.py`.
5. **L3 (clone) and L3m:**
   - settle, collect and check (`expected-today.json` / `expected-mechanism.json`): 0 new;
   - `perf_budget.py --database-url` in **report mode** on both, cold and warm, with and without `If-None-Match`;
   - the packet tables vs §11b.
6. **Guards:**
   - A, W, N, V, M, L, D (plan §4.3);
   - the new graph check, `perf_budget.py --fixture` and the hard-wiring ratchet, each run directly;
   - the estate guard self-tests only if P3 needs a `configuration-persistence.ps1` edit.

## 6. Pre-flight (answer from code, batch them, then stop)

- **P1.** Re-anchor every CH-5a2 name used here (`chain_api`, `refs`, `read`, `routeFor`, `chainClient`) to merged `path:line`.
- **P2.** Where startup validation can run without blocking tests that build the app without config (the app factory in `B/main.py`). Name the hook.
- **P3.** Does rule 8 of the estate guard need the new readers (`etag.py` reads `event_outbox`, `site_day_snapshot`, `finding_thread_event`)? State the lines.
- **P4.** The current counts for every R7 pattern per file. Commit them as the baseline, and list the files that R8 drops.
- **P5.** Every consumer of the three old list components and of the frame switch (tests, captures, the navigation-truthfulness inventory).
- **P6.** `MA-1-mock-measurements.md` widths for the Why dialog and the row button at 1440/390 px. These are the block's size budget.

## 7. Review focus

- The trace is computed from stored ids only. The browser renders `text`, never builds it.
- The ETag covers every input the body depends on. Test it by flipping each one.
- No budget value is edited to pass. The DB mode reports and E4 enforces.
- No outcome id or Site-type literal in `F/blocks/`. The ratchet only shrinks.
- The blocks reproduce the MA-1 markup. Every departure is labelled.

## Revision OWN-CH5c (Architect 6, Claude, 2026-11-04). This supersedes the lines it names.

- **Order.** The branch is cut from main after **CH-5c** merges (lane 1: CH-5a2 → CH-5c → CH-5b), not straight after CH-5a2.
- **R4 is superseded.** The watermark is CH-5c's `B/chain/watermark.py` (CH5c-R3 R7). The ETag **is** the stored response's `etag` column (CH5c-R3 R6). A route that CH-5c does not store computes the same `etag` function over the same watermark. `B/chain/etag.py` shrinks to a re-export, or is not created, and "No server-side body memo in this slice" is void. A `304` is answered after the watermark statement alone, with no composition and no store read.
- **Tests.** The R4 flip tests move to CH-5c. CH-5b keeps:
  - `304` on a matching `If-None-Match`;
  - a new tag after `late_fill(KOBO-001, D7)`, with the Cold tag unchanged;
  - the client reusing the body on `304`.
- **Size: 6 → 5.5.** The watermark and its flip tests are now in CH-5c.

## Build units (split 2026-11-05)

- Architect: Claude (Architect 13), 2026-11-05, under the owner's efficiency rule (`.ai/ROLE_CONFIG.md` "Token Efficiency", demo-sprint additions; `.agent/owner-efficiency-2026-11-05.md`). Plan row **SPLIT-1**. Nothing in §0–§7 or the Revision OWN-CH5c changes; this section only cuts the 5.5 units into three builder units.
- **Total unchanged: 5.5** (1.5 + 2 + 2).
- **Common rules for every unit.**
  - One branch per unit (`task/<unit-id>-…`), cut from main after the unit's dependency merges. Each unit merges on its own review ACCEPT (or after the batched review it is paired with).
  - The builder reads **only** its reading budget below, plus targeted greps of the code it edits. No plan HTML, no other slices' sheets, no whole-file reads of the design proposal.
  - Pre-flight items are answered by each unit's first builder (Opus) for its own unit only, batched, then it stops for rulings. Answers go to `.agent/<unit-id>-preflight.md`. The next unit's builder reads the earlier units' merged code by grep, not their packets.
  - Continuation builders and fix rounds use Sonnet from a precise handoff. Builder replies are 10 lines or fewer.

| Unit | Size | Scope (this sheet) | Depends on | Review |
|---|---|---|---|---|
| **CH-5b1** guards and tools | 1.5 | §0 bullets "Budget guard", "Graph check", "Hard-wiring guard"; R5, R6, R7; §3 rows `B/chain/graph.py`, `B/main.py`, `config/chain/perf-budgets-v1.json`, `tools/checks/perf_budget.py` (+ fixtures), `tools/checks/frontend-hardwiring.mjs` (+ baseline), `tools/check-all.ps1`; pre-flight P2, P4 | CH-9 merged (it is the next lane-2 item, see the lane move) | Own review (new guard logic) |
| **CH-5b2** "Why?" trace and ETag/304, server | 2 | §0 bullets "Why?" and "ETag"; R1–R4 as revised by OWN-CH5c; §2.1, §2.2 server half, §2.3; §3 rows `why.py`, `etag.py` (re-export or none), `chain_api.py`, `vocabulary.py`; pre-flight P1 (backend names), P3 | CH-5c2 merged (lane 1) | Own review (contract and tag correctness) |
| **CH-5b3** shared blocks, "Why?" dialog, one finding list, client 304 | 2 | §0 bullets "Shared blocks", "One finding list"; R8, R9; §2.2 client half; §3 `F/` rows; §4 whole; pre-flight P1 (frontend names), P5, P6 | CH-5b1 and CH-5b2 merged | Own review (mock fidelity; MOCK DEVIATION labels) |

### CH-5b1 (1.5): graph check, budget guard, hard-wiring ratchet

- **Reading budget.**
  - This sheet: §0 the three named bullets; §1 R5, R6, R7; §3 the six named rows; §5 item 1 last bullet (graph check) and item 6; §6 P2, P4.
  - `Docs/demo-sprint/implementation-logic-design-proposal.html` §11b, the budget table only (grep `perf-budget` / `11b`); §13, the pattern list only.
  - Code, by grep: the app factory in `B/main.py`; `chain_perf_probe` (CH-5a1); `config/chain/event-register-v1.yaml`; `B/chain/measures.py` `MEASURES`; `config/chain/thread-lifecycle-v1.json` `clean_day_measures`; `B/outcomes/outcome_map.py` `ENTRIES`; `tools/check-all.ps1`.
- **Acceptance.**
  - L0 `backend/tests/test_ch5b_graph.py`: passes on main's config; fails on one mutation per R6 rule.
  - `perf_budget.py --fixture` self-test passes; `--database-url` runs once on the polish clone in **report mode** and the packet lists the numbers (no budget edited).
  - The ratchet run directly: the baseline equals today's counts (P4 table in the packet); a rise in one file fails; `--shrink` never raises a count.
  - The startup hook (P2) refuses to start on a broken config and does not break the tests that build the app without config.
  - `Docs/demo-sprint/chain-graph.svg` generated and committed.
  - Guards A, W, N, V, M, L, D, and the three new checks each run directly.
- **Lane move: lane 1 → lane 2.** It needs only merged code (CH-1b register, CH-5a1 probe, `outcome_map`), and no lane-1 unit before CH-5b3 reads it. It must merge before CH-5b3 (the blocks are born at 0 under the ratchet) and before CH-6a1 (the strategy load-time check sits beside the graph check in `B/main.py`). On lane 2 it runs straight after CH-9, which is ahead of both.

### CH-5b2 (2): the trace, the two "Why?" routes, ETag and 304

- **Reading budget.**
  - This sheet: §0 bullets "Why?" and "ETag"; §1 R1–R4; the Revision OWN-CH5c (R4 is superseded there); §2.1–§2.3; §3 the four named rows; §5 item 1 (trace and ETag bullets), item 2, item 4 backend lines; §6 P1, P3; §7 bullets 1–2.
  - Design §5b.5 only.
  - `.agent/build-sheet-CH-5c.md`: the CH5c-R3 R6/R7 rows (watermark and stored `etag`) and §8.6/§8.7 headings for `valid_until` (grep `etag`, `watermark`, `valid_until`); nothing else.
  - Code, by grep: `B/chain_api.py`, `B/chain/watermark.py`, `B/chain/vocabulary.py`, `outcome_map` `categories_for` / `thread_signal_key`, `.agent/build-sheet-MD-0.md` §7 (the Kobo D-days only).
- **Acceptance.**
  - L0 `test_ch5b_why.py`: each category × Site type, including COMPLETE, GAP-K7 → `why.change.days`, open thread without Action → `why.change.action`, CHANGE_APPLIED → `why.change.verdict`; no node without ids; `text` equals the §2.3 literals; `CATEGORY_UNKNOWN` 422; the estate shape sums no money.
  - L2m `test_ch5b_why_postgres.py`: Kobo D13 OPTIMIZE_COST trace ≤ 50 ms (5-run median, reported) with the D4/D11 Findings and ACT-K1's verification; a `304` round trip on every chain and why route; after `late_fill(KOBO-001, D7)` the Kobo tag changes and the Cold tag does not. A `304` is answered after the watermark statement alone (no composition, no store read), asserted with the CH-5a1 ledger.
  - Scoped existing: `test_ch5a2_*`, `test_out_b4_route.py`, `tools/checks/test_chain_coherence.py`, the CH-5c/5c2 store tests (grep `test_ch5c`).
  - Guards A, W, N, V, M, L, D; the CH-5b1 checks.
- **No frontend in this unit.** The routes are additive and unused until CH-5b3, so the unit merges alone safely.

### CH-5b3 (2): blocks, the dialog, ThreadList and the client

- **Reading budget.**
  - This sheet: §0 bullets "Shared blocks" and "One finding list"; §1 R8, R9; §2.2 last bullet; §3 the `F/` rows; §4; §5 item 3, item 4 frontend lines, item 5; §6 P1 (`routeFor`, `chainClient`), P5, P6; §7 bullets 4–5.
  - Mock: `frontend/mockups/v70/outcomes.js:115-200` only; `.agent/MA-1-mock-measurements.md` (the Why dialog, row button, `ob`/`ob-days` rows).
  - Code: `F/sites/OutcomeBoard.tsx:60-320` (rows and `ExplainerDialog`), `F/estate/PortfolioOutcomes.tsx:100-280`, `F/shell/SiteAnalyticsFrames.tsx:460-600`, `F/sites/SiteFindingIndex.tsx:90-140`, `F/App.tsx` route table (grep `findings`), `F/shell/chainClient.ts`. Not the rest of `SiteFindingIndex.tsx`.
- **Acceptance.**
  - Vitest `npx vitest related --run src/blocks/*.tsx src/sites/OutcomeBoard.tsx src/estate/PortfolioOutcomes.tsx src/shell/SiteAnalyticsFrames.tsx`: blocks from the L1 goldens; Why opens, traps focus, closes, and is a bottom sheet at 390 px; ThreadList per lens and Site type, plus the synthetic fourth Site type with no code change; `304` reuse in the client.
  - Scoped existing: `outcomeBoard.test.tsx`, `estatePortfolio.test.tsx`, `s404SiteFindingIndex.test.tsx`.
  - The ratchet: `--shrink` after the R8 removals; every `F/blocks/` file at 0; no file rises.
  - L3 (clone) and L3m: settle, collect and check: 0 new. `perf_budget.py --database-url` in report mode on both, cold and warm, with and without `If-None-Match`; packet tables against §11b.
  - Captures at 1440/390 of the board, Portfolio and Site Findings (All + three lenses) against the MA-1 mock; MD-CH5b-1/2/3 labelled in the packet.
  - Guards A, W, N, V, M, L, D.
