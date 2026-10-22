# W5-01b review (C4 cold scenarios backend + C5 cold Scenarios page)

Reviewer: fresh independent Claude reviewer, 2026-10-22. Did not author any of this work.
Branch `task/W5-01b-cold-scenarios`, head `1213c36b` (worktree `AssetOpsV1-review4`); merge-base with main
`d9d96744` = current main tip. Code reviewed = `7a74c61b` (the last code commit; `1213c36b` changes only
`.agent/` captures, `capture.mjs`, `evidence.json` and the handoff). Diff: `git diff main...HEAD -- backend frontend tools contracts`
(46 files, +3462/-53; no `contracts/` change).

## Verdict

**REVISE** — one High (by the ROLE_CONFIG mock-fidelity rule) that needs an Architect ruling, not new
implementation design; everything else in C4/C5 and the Q-C5b/Q-C5c rulings is built as ruled and verified.

## Findings

### H1 — `Scenarios created through …` line is an unlabelled departure from the v69 `cold-scenarios` mock (ruling gap)

- Where: `frontend/src/sites/ColdScenarios.tsx:306-308` (`<p className="cold-scenarios-through" data-scenarios-through>`),
  rendered on every loaded state including the empty state (`cold-scenarios-empty-{1440,390}-app.png`).
- What: the v69 `cold-scenarios` screen (`index.html` `scenariosScreen`) is exactly panel → blue notice. The app adds,
  above the panel, a `Scenarios created through {scenario_at}` line. It was ruled (P-C5-9..16: "Show
  `SelectedWindowBar` … and `Scenarios created through {scenario_at UTC}`"), but the ruling does not label it
  `MOCK DEVIATION`, and the same ruling set says for P-C5-1..5 "Restore exact empty form/copy; no extra status
  strip … no other mock departure is authorized". The code carries no `MOCK DEVIATION` comment for it, and the
  builder's own `evidence.json` `comparison.unlabelled_differences` lists it. ROLE_CONFIG: "An unavoidable deviation
  is labelled `MOCK DEVIATION` in the ruling … Reviewers treat an unlabelled deviation as High."
- Why it matters: it is user-visible on every state, including the empty state the ruling said to restore exactly,
  and it is the only user-visible departure on this screen without a label and stated reason for the owner relay.
- Fix (Architect, then a one-line code comment): either (a) label it in the spec as `MOCK DEVIATION — authored clock`
  (mock element: none; why: an authored list read at an explicit `scenario_at` must state its authored as-of time, the
  mock's topbar window only carries the evidence window; alternatives considered) and add the matching
  `{/* MOCK DEVIATION — … */}` comment in `ColdScenarios.tsx`; or (b) drop the line and keep `scenario_at` only in the
  address. The implementer must not choose. Not an implementer defect: the builder followed P-C5-15 and flagged it.
- Not included in H1: the `Selected window … / Selected evidence through …` date bar. It is the cold Site frame's
  established rendering of the mock's selected window (W2-04 build spec: "All five routes keep the mock's local Site
  tabs, selected date bar"), shared by every merged cold page; I treat it as the existing cold-frame element, not a
  new departure of this slice. The breadcrumb ending `Scenarios` is the card's ruled breadcrumb and the same pattern
  as the merged Cooling/Health siblings. If the Architect disagrees on either, it belongs in the same H1 label.

### Asked: the raw ISO `Window` line — ruled and labelled, not a finding

`Basis` expansion `Window` → `2026-10-06T19:00:00.000000Z – 2026-10-06T20:05:00.000000Z`
(`ColdScenarios.tsx:139-144`). The mock has no expansion and no window line in this panel at all; the
`Review assumptions →` disclosure is part of the ruled, labelled `MOCK DEVIATION — authored rows` ("real C4
definitions replace that block with the card's table, disclosure and pager"), and its content is spec-verbatim:
closure 2 "`Window` → `authored_basis.from` – `authored_basis.to` (ISO, verbatim)", P-C5-20 "`Window` is
`{from} – {to}`". So it is a ruled difference inside a labelled deviation, not an unlabelled mock departure. The
builder's note ("not formatted {from} – {to}") misreads P-C5-20; the form matches. See L2 for the presentation note.

### L1 — a 409 `COLD_SCENARIO_CURSOR_BASIS_CHANGED` on page 2 cannot be recovered in-page (Low, spec gap)

- Where: `ColdScenarios.tsx:363` (`ScenariosRefusal` `onRetry` only bumps `attempt`; `cursors` state is kept).
- What: if evidence advances between page 1 and `Next` (tested in C4 at `test_w501_cold_scenarios_postgres.py:570`),
  the page shows the refusal with the server message "Start at the first page.", but `Retry` resends the same stale
  cursor and the refusal has no `First page` control; only a reload or navigating away recovers. The same applies if
  the address window changes while the component stays mounted with a cursor.
- Why Low: ruled behaviour ("`Retry` is a button that refetches the same URL") and only reachable after paging past
  50 rows while evidence moves. Fix if the Architect wants it: on a 409 basis-changed refusal, clear `cursors`
  on Retry (or show `First page`). Not required for merge.

### L2 — mixed date formats on one page (Low, presentation; batch to the UI/UX pass)

On the same page the date bar reads `22 Oct 20:07:37 UTC`, `Scenarios created through 2026-10-22 20:08 UTC`, the
Basis cell `2026-10-22 20:07 UTC`, and the expansion raw ISO with six fractional digits. All are ruled or
spec-verbatim formats; this is a client-facing polish item for the W1-conclusion plain-language pass, not a fix here.

No other finding. I looked specifically for and did not find: a missing card/file ownership, a wrong migration
parent or head, an unsafe downgrade, a writer-policy hole, a fabricated 409, a partial 200 on malformed history, an
outcome/revenue field, an ordinary-viewer create control, or a missing `total_pages` validation.

## Checklist from the dispatch

| Item | Result |
| --- | --- |
| Every changed file on a card | Yes. C4: migration, `cold_scenarios/{__init__,rules,store,service}.py` (the `__init__` is the package marker of the listed new package), `cold_scenarios_api.py`, `main.py`, `analytics/cold_depth.py` (`basis_on` only), both rule-8 tools, `test_w501_cold_scenarios_postgres.py`, the 16 P-C4-1 files. C5: card list + V69Layout, productVocabulary.{json,ts}, coldSiteViews.test (P-C5-1..8), coldScenarios.css (P-C5-13), miniDecisions.test (Q-C5b-1), RailIcon.tsx (Q-C5c-1). Nothing outside. |
| Migration `0032` parent/head/downgrade | `revision="0032_w5_cold_scenarios"`, `down_revision="0030_w4_mini_decisions"`; sole head (asserted in `test_migration_constraints` and w403). Schema matches the C4 literal (names, checks, FKs, uniques; index on the revision table `(tenant_id,site_id,recorded_at DESC,id DESC)` per P-C4-4), both `_immutable` triggers on `ledger_append_only()`. Downgrade: ACCESS EXCLUSIVE locks child-first, refuses any row with the exact ruled message, then drops triggers, index, revision, root, sequence. No cascade. Safe. |
| 16 head-pin edits | Correct per the P-C4-1 table: only latest-head/rollback assertions moved to 0032; `mini_depth_probe` asserts empty 0032 and traverses it before 0029; w403 keeps `HEAD=0030`, adds `LATEST_HEAD`, and `to_0030()` crosses empty 0032 before every 0030 downgrade; 0030 refusal/catalog expectations kept. |
| Writer-probe placement / rule 8 | `COLD_SCENARIO` beside `DECISION`; helper defs + `NEGATIVE +=` after `decision truncate`; `WRITER_CONTROLS +=` after the decision controls (after `WRITER_CONTROLS`/`_work_control` exist) — no NameError (check-all imports it). `configuration-persistence.ps1` steps 1-6 match the literal policy. Store has no `ON CONFLICT`, every INSERT is one `"INSERT INTO <table> (` literal. |
| Vocabulary-scan change | `screenGlosses` keyed by screen ID, exact case-sensitive removal longest-first, only when `screen` is passed; global glosses and T028 terms untouched. Gloss texts = the allowed P-C5-6/7/8 list + the three Q-C5b-3 texts with the confirmed `why`. coldSiteViews proves the live link passes and a planted `scenarios`/`draft` still fails. |
| DTO `total_pages` | Server: same snapshot and same `_SELECTED` filters as `items`, before cursor/limit, `ceil(count/limit)`, `0` when empty. Client: required nonnegative integer; missing/null/string/fractional/negative are malformed (tests). Counter `{n} of {total}` after `Next`; nav absent for the empty block. |
| Malformed-revision 503 | Candidate shape check (`_MALFORMED`) before the cutoff predicate (Q-C5b-5) and the Site-wide revision-1 `from`/`to` preflight (`_MALFORMED_ROOT`) after `scenario_at`/basis and before the candidate block (Q-C5c-3), both `DECISION_STORE_UNAVAILABLE` in `{error}`; tests cover missing from/to/cutoff, `limit=1`, other Site not poisoned, earlier `scenario_at` still lists. |
| Pager + basis scroller at both widths | 1440: `.cold-scenarios-basis` 360px/`overflow-y:auto`, expanded panel 615/650. 390: Q-C5c-2 literal phone rule present verbatim; capture layout assertion (evidence.json, revision `7a74c61b`): panel 475-490/560, basis 220px auto, Basis cell 280≥190, table scroller 820>318 with last column reachable, document 390=390. Pager `1 of 1` visible at both widths; `1 of 2`/`2 of 2` in vitest. |
| `RailIcon` info icon | `RAIL_ICON_PATHS.info` = exact v69 path; notice children `<RailIcon name="info" /><p>…</p>`; flex CSS as ruled; no page-module `<svg`; visible in captures at both widths. |
| Mock restores | Site-name h1, `Financials · scenarios (placeholder)` (separate `coldScenarios` key; mini `scenarios` unchanged), panel subtitle `Placeholder · to be designed with the owner`, evidence-icon empty block with the mock h3/paragraph, blue closing notice after the panel. Side-by-side with the mock at 1440/390: equal apart from H1 and the cold-frame date bar/breadcrumb noted above. |
| Two labelled MOCK DEVIATIONs | Both present in code as ruled: authored rows (table, disclosure, pager inside the titled/subtitled panel) and the amber currentness notice above the panel (absent for `CURRENT`; HISTORICAL literal is the Q-C5b-3 text). |
| Builder's confirmed choices (Q-C5b-7) | All as listed: JSON-object check names; correction hash = body + root ID + resolved window/cutoff (no site_id); cursor binds `limit` (explicit different limit → 409, tested); actor authorization before body; `basis_on` failure → 503 `COLD_READ_UNAVAILABLE`; fixed ISO 4217 list, no coercion; repeated keys → `COLD_PARAMETER_UNKNOWN` in `{error}`. |

## Checks I ran (on `1213c36b`, code = `7a74c61b`)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `tools/check-all.ps1 -Python <plan2 venv>`: **All 11 guards passed** (incl. architecture seams/shell-overflow,
  navigation truthfulness + rail fixtures, dependency registry, screen ledger, estate self-tests).
- Backend focused, private DB `assetops_w501brev_test` (template routing on), `-p no:xdist`:
  `test_w501_cold_scenarios_postgres.py test_w403_migration_postgres.py test_w501_cold_depth_postgres.py test_w501_cold_depth_router.py`
  → **34 passed, 0 skipped, 0 failed, 452 s**.
- Backend head-pin modules (the other 14 P-C4-1 files): **184 passed, 0 skipped, 0 failed, 973 s** (same private DB). With w403 above, all 16 P-C4-1 files pass at head 0032.
- `npx.cmd tsc --noEmit` (frontend): clean, exit 0.
- `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` coldScenarios, coldSiteViews, coldRoutes, miniDecisions:
  **4 files, 181 passed** (vitest did run on this machine).
- Not run: `npm.cmd run build` (memory), browsers/captures and `tools/writer_guard_probes.py --seam` (it edits
  source files in place; the builder's seam run is cited: 11 `cold-scenario` CAUGHT, 2 controls ALLOWED on a clean
  tree). Captures inspected from `.agent/W5-01b-C5-evidence/` (taken on `7a74c61b`, identical code).
- DB `assetops_w501brev_test` and its run databases dropped; no processes left running.

## Residual risk / merge preconditions not covered by the packet

- **Full backend suite not run on this revision.** 0032 is a migration and the slice touches `main.py`,
  `tools/checks/*` and `writer_guard_probes.py`, so ROLE_CONFIG tiered testing requires one full backend suite
  before merge. The handoff records none ("Full backend suite not run (per dispatch)"). I did not run it (dispatch
  scope, memory). It must run on the final head before merge.
- Full frontend vitest suite (slice-merge scoped regression) and `npm.cmd run build` on the final head are not in
  the packet for `7a74c61b`; the builder's 27-file/1017 run was on `4edcf560`.
- W5-02 `0033` must name `0032_w5_cold_scenarios` as parent (spec states it).
- `main.py` creates a second SQLAlchemy engine/pool for the cold scenario store when cold reads are configured
  (spec literal); acceptable, noted for connection budgeting.
